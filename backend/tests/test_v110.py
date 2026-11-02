"""v1.10 acceptance regressions: server-verified saves and payments."""
import hashlib
import hmac
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.accounts import AccountStore
from app.models import BirthData
from app.payment import OrderStore, check_verified_payment, verify_webhook_v3, payment_ready

BIRTH={"name":"Example","year":2002,"month":1,"day":25,"hour":9,"minute":30,
       "latitude":40.872,"longitude":35.464,"tz_offset_hours":2.0,"timezone":"Europe/Istanbul","house_system":"P"}

class AccountAcceptanceTests(unittest.TestCase):
    def test_create_get_rename_list_relogin_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{"DATABASE_URL":"sqlite:///"+str(Path(tmp)/"account.db")},clear=False):
                with TestClient(app) as client:
                    one=client.post('/api/account/register',json={"email":"u1@sample.test","password":"super-secure-pass","display_name":"One"})
                    self.assertEqual(one.status_code,200,one.text)
                    token=one.json()['token'];header={"Authorization":f"Bearer {token}"}
                    second=client.post('/api/account/register',json={"email":"u2@sample.test","password":"super-secure-pass","display_name":"Two"})
                    other={"Authorization":f"Bearer {second.json()['token']}"}
                    saved=client.post('/api/account/charts',headers=header,json={"label":"Crush ✨","birth":BIRTH})
                    self.assertEqual(saved.status_code,200,saved.text)
                    chart_id=saved.json()['chart']['id']
                    self.assertIn('chart',saved.json()['chart']['natal_snapshot'])
                    self.assertEqual(client.get('/api/account/charts/'+chart_id,headers=other).status_code,404)
                    self.assertEqual(client.patch('/api/account/charts/'+chart_id,headers=other,json={"label":"Hacked"}).status_code,404)
                    renamed=client.patch('/api/account/charts/'+chart_id,headers=header,json={"label":"Partner ❤️"})
                    self.assertEqual(renamed.status_code,200,renamed.text)
                    self.assertEqual(renamed.json()['chart']['label'],"Partner ❤️")
                    client.post('/api/account/logout',headers=header,json={})
                    self.assertEqual(client.get('/api/account/me',headers=header).status_code,401)
                    login=client.post('/api/account/login',json={"email":"u1@sample.test","password":"super-secure-pass"})
                    self.assertEqual(login.status_code,200,login.text)
                    again={"Authorization":"Bearer "+login.json()['token']}
                    self.assertEqual(client.get('/api/account/me',headers=again).json()['charts'][0]['label'],"Partner ❤️")
                    self.assertIsNotNone(client.get('/api/account/charts/'+chart_id,headers=again).json()['chart']['natal_snapshot'])

    def test_config_unavailable_does_not_claim_ready(self):
        with patch.dict(os.environ, {"DATABASE_URL":"", "ENVIRONMENT":"production"},clear=False):
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/account/config').json()['ready'],False)

class PaymentAcceptanceTests(unittest.TestCase):
    def test_safe_by_default_without_live_merchant_keys(self):
        with patch.dict(os.environ,{"PAYMENTS_ENABLED":"false"},clear=False):
            self.assertFalse(payment_ready())
        with patch.dict(os.environ,{"PAYMENTS_ENABLED":"true","PAYMENT_MODE":"live","IYZICO_BASE_URL":"https://sandbox-api.iyzipay.com","IYZICO_API_KEY":"sandbox-demo","IYZICO_SECRET_KEY":"secret","DATABASE_URL":"postgresql://not-real"},clear=False):
            self.assertFalse(payment_ready())

    def test_signed_iyzico_webhook_v3_tamper_protection(self):
        payload={"iyziEventType":"CHECKOUT_FORM_AUTH","iyziPaymentId":123,"token":"tok_123","paymentConversationId":"ord_123","status":"SUCCESS"}
        secret="a-test-secret-not-a-real-merchant-key"
        with patch.dict(os.environ,{"IYZICO_SECRET_KEY":secret},clear=False):
            body=secret+"".join(str(payload[k]) for k in ("iyziEventType","iyziPaymentId","token","paymentConversationId","status"))
            sig=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()
            self.assertTrue(verify_webhook_v3(payload,sig))
            self.assertFalse(verify_webhook_v3({**payload,"status":"FAILURE"},sig))
            self.assertFalse(verify_webhook_v3(payload,""))

    def test_order_exact_match_and_idempotent_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{"DATABASE_URL":"sqlite:///"+str(Path(tmp)/"orders.db"),"ENVIRONMENT":"development"},clear=False):
                store=OrderStore()
                order=store.create(product='personalized_reading',tier='personalized',amount='499.00',email='u@example.test',request_payload={})
                store.set_payment_token(order.id,'token-x')
                order=store.get_id(order.id)
                verified={"status":"success","paymentStatus":"SUCCESS","conversationId":order.id,"basketId":order.id,"token":"token-x","currency":"TRY","paidPrice":"499.00","price":"499.00","paymentId":"pi_x"}
                self.assertTrue(check_verified_payment(verified,order))
                for change in ({"paidPrice":"1.00"},{"basketId":"other"},{"conversationId":"other"},{"token":"different"},{"currency":"USD"},{"paymentStatus":"FAILURE"},{"paymentId":""}):
                    self.assertFalse(check_verified_payment({**verified,**change},order))
                store.mark_paid(order.id,'pi_x')
                store.mark_failed(order.id)
                store.mark_paid(order.id,'pi_x')
                self.assertEqual(store.get_id(order.id).status,'paid')

    def test_callback_must_retrieve_and_verify_before_unlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{"DATABASE_URL":"sqlite:///"+str(Path(tmp)/"callback.db"),"ENVIRONMENT":"development"},clear=False):
                store=OrderStore()
                order=store.create(product='personalized_reading',tier='personalized',amount='499.00',email='u@example.test',request_payload={})
                store.set_payment_token(order.id,'token-actual')
                response={"status":"success","paymentStatus":"SUCCESS","conversationId":order.id,"basketId":order.id,"token":"token-actual","currency":"TRY","price":"499.00","paidPrice":"499.00","paymentId":"pm_321"}
                with patch('app.main.retrieve_checkout',return_value={**response,"paidPrice":"0.01"}):
                    with TestClient(app) as client:
                        r=client.post('/api/payments/iyzico/callback?order='+order.id,data={'token':'token-actual'},follow_redirects=False)
                        self.assertEqual(r.status_code,303)
                        self.assertIn('payment=failed',r.headers['location'])
                self.assertNotEqual(store.get_id(order.id).status,'paid')
                with patch('app.main.retrieve_checkout',return_value=response), patch('app.main.send_payment_receipt') as mail:
                    with TestClient(app) as client:
                        r=client.post('/api/payments/iyzico/callback?order='+order.id,data={'token':'token-actual'},follow_redirects=False)
                        self.assertIn('payment=success',r.headers['location'])
                        r=client.post('/api/payments/iyzico/callback?order='+order.id,data={'token':'token-actual'},follow_redirects=False)
                        self.assertIn('payment=success',r.headers['location'])
                    self.assertEqual(mail.call_count,1)
                self.assertEqual(store.get_id(order.id).status,'paid')

    def test_valid_webhook_gets_independent_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret='safe-test-secret'
            with patch.dict(os.environ,{"DATABASE_URL":"sqlite:///"+str(Path(tmp)/"webhook.db"),"ENVIRONMENT":"development","IYZICO_SECRET_KEY":secret},clear=False):
                store=OrderStore()
                order=store.create(product='deep_reading',tier='deep',amount='899.00',email='u@example.test',request_payload={})
                store.set_payment_token(order.id,'token-actual')
                payload={"iyziEventType":"CHECKOUT_FORM_AUTH","iyziPaymentId":123,"token":"token-actual","paymentConversationId":order.id,"status":"SUCCESS"}
                body=secret+''.join(str(payload[k]) for k in ("iyziEventType","iyziPaymentId","token","paymentConversationId","status"))
                sig=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()
                verified={"status":"success","paymentStatus":"SUCCESS","conversationId":order.id,"basketId":order.id,"token":"token-actual","currency":"TRY","price":"899.00","paidPrice":"899.00","paymentId":"pm_321"}
                with patch('app.main.payment_ready',return_value=True),patch('app.main.retrieve_checkout',return_value=verified) as retrieve,patch('app.main.send_payment_receipt') as mail:
                    with TestClient(app) as client:
                        r=client.post('/api/payments/iyzico/webhook',headers={'X-IYZ-SIGNATURE-V3':sig},json=payload)
                        self.assertEqual(r.status_code,200,r.text)
                        self.assertEqual(store.get_id(order.id).status,'paid')
                    retrieve.assert_called_once()
                    mail.assert_called_once()

    def test_webhook_without_signature_is_rejected(self):
        with patch('app.main.payment_ready',return_value=True):
            with TestClient(app) as client:
                response=client.post('/api/payments/iyzico/webhook',json={"status":"SUCCESS"})
                self.assertEqual(response.status_code,403)

if __name__=='__main__':unittest.main()

class PopularSkyTests(unittest.TestCase):
    def test_mercury_and_saturn_snapshot_comes_from_positions(self):
        from app.chart import compute_natal_chart
        from app.transits import compute_personal_transits
        from app.models import BirthData
        from datetime import date
        birth=BirthData(**BIRTH)
        natal=compute_natal_chart(name='Example',year=2002,month=1,day=25,hour=9,minute=30,latitude=40.872,longitude=35.464,tz_offset_hours=2,house_system='P')
        sky=compute_personal_transits(natal,birth,target_date=date(2026,11,2))['popular_sky']
        self.assertIn(sky['mercury_retrograde'],[True,False])
        self.assertTrue(0<=sky['saturn_return_distance_deg']<=180)
        self.assertEqual(sky['saturn_return_within_3deg'],sky['saturn_return_distance_deg']<=3)
