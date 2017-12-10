# Mirocana Alpha


Create, test and evaluate your own trading strategies with Mirocana core.


* `git clone https://github.com/mirocana/alpha.git`
* `cd alpha`
* `pip install virtualenv`
* `virtualenv _env -p python3`
* `. _env/bin/activate`
* `pip install -r requirements.txt`
* `python strategies/testing.py`


AVAILABLE INSTRUMENTS FOR CURRENCY MARKET:

```
┌─symbol_ticket─┐
│ AU200_AUD     │
│ AUD_CAD       │
│ AUD_CHF       │
│ AUD_HKD       │
│ AUD_JPY       │
│ AUD_NZD       │
│ AUD_SGD       │
│ AUD_USD       │
│ BCO_USD       │
│ CAD_CHF       │
│ CAD_HKD       │
│ CAD_JPY       │
│ CAD_SGD       │
│ CHF_HKD       │
│ CHF_JPY       │
│ CHF_ZAR       │
│ CN50_USD      │
│ CORN_USD      │
│ DE10YB_EUR    │
│ DE30_EUR      │
│ EU50_EUR      │
│ EUR_AUD       │
│ EUR_CAD       │
│ EUR_CHF       │
│ EUR_CZK       │
│ EUR_DKK       │
│ EUR_GBP       │
│ EUR_HKD       │
│ EUR_HUF       │
│ EUR_JPY       │
│ EUR_NOK       │
│ EUR_NZD       │
│ EUR_PLN       │
│ EUR_SEK       │
│ EUR_SGD       │
│ EUR_TRY       │
│ EUR_USD       │
│ EUR_ZAR       │
│ FR40_EUR      │
│ GBP_AUD       │
│ GBP_CAD       │
│ GBP_CHF       │
│ GBP_HKD       │
│ GBP_JPY       │
│ GBP_NZD       │
│ GBP_PLN       │
│ GBP_SGD       │
│ GBP_USD       │
│ GBP_ZAR       │
│ HK33_HKD      │
│ HKD_JPY       │
│ IN50_USD      │
│ JP225_USD     │
│ NAS100_USD    │
│ NATGAS_USD    │
│ NL25_EUR      │
│ NZD_CAD       │
│ NZD_CHF       │
│ NZD_HKD       │
│ NZD_JPY       │
│ NZD_SGD       │
│ NZD_USD       │
│ SG30_SGD      │
│ SGD_CHF       │
│ SGD_HKD       │
│ SGD_JPY       │
│ SOYBN_USD     │
│ SPX500_USD    │
│ SUGAR_USD     │
│ TRY_JPY       │
│ TWIX_USD      │
│ UK100_GBP     │
│ UK10YB_GBP    │
│ US2000_USD    │
│ US30_USD      │
│ USB02Y_USD    │
│ USB05Y_USD    │
│ USB10Y_USD    │
│ USB30Y_USD    │
│ USD_CAD       │
│ USD_CHF       │
│ USD_CNH       │
│ USD_CZK       │
│ USD_DKK       │
│ USD_HKD       │
│ USD_HUF       │
│ USD_INR       │
│ USD_JPY       │
│ USD_MXN       │
│ USD_NOK       │
│ USD_PLN       │
│ USD_SAR       │
│ USD_SEK       │
│ USD_SGD       │
│ USD_THB       │
│ USD_TRY       │
│ USD_ZAR       │
│ WHEAT_USD     │
│ WTICO_USD     │
│ XAG_AUD       │
│ XAG_CAD       │
│ XAG_CHF       │
│ XAG_EUR       │
│ XAG_GBP       │
│ XAG_HKD       │
│ XAG_JPY       │
│ XAG_NZD       │
│ XAG_SGD       │
│ XAG_USD       │
│ XAU_AUD       │
│ XAU_CAD       │
│ XAU_CHF       │
│ XAU_EUR       │
│ XAU_GBP       │
│ XAU_HKD       │
│ XAU_JPY       │
│ XAU_NZD       │
│ XAU_SGD       │
│ XAU_USD       │
│ XAU_XAG       │
│ XCU_USD       │
│ XPD_USD       │
│ XPT_USD       │
│ ZAR_JPY       │
└───────────────┘
```


AVAILABLE INSTRUMENTS FOR CRYPTO-CURRENCY MARKET:

```
┌─symbol_ticket─┐
│ BTC_AMP       │
│ BTC_ARDR      │
│ BTC_BCH       │
│ BTC_BCN       │
│ BTC_BCY       │
│ BTC_BELA      │
│ BTC_BLK       │
│ BTC_BTCD      │
│ BTC_BTM       │
│ BTC_BTS       │
│ BTC_BURST     │
│ BTC_CLAM      │
│ BTC_CVC       │
│ BTC_DASH      │
│ BTC_DCR       │
│ BTC_DGB       │
│ BTC_DOGE      │
│ BTC_EMC2      │
│ BTC_ETC       │
│ BTC_ETH       │
│ BTC_EXP       │
│ BTC_FCT       │
│ BTC_FLDC      │
│ BTC_FLO       │
│ BTC_GAME      │
│ BTC_GAS       │
│ BTC_GNO       │
│ BTC_GNT       │
│ BTC_GRC       │
│ BTC_HUC       │
│ BTC_LBC       │
│ BTC_LSK       │
│ BTC_LTC       │
│ BTC_MAID      │
│ BTC_NAUT      │
│ BTC_NAV       │
│ BTC_NEOS      │
│ BTC_NMC       │
│ BTC_NOTE      │
│ BTC_NXC       │
│ BTC_NXT       │
│ BTC_OMG       │
│ BTC_OMNI      │
│ BTC_PASC      │
│ BTC_PINK      │
│ BTC_POT       │
│ BTC_PPC       │
│ BTC_RADS      │
│ BTC_REP       │
│ BTC_RIC       │
│ BTC_SBD       │
│ BTC_SC        │
│ BTC_SJCX      │
│ BTC_STEEM     │
│ BTC_STORJ     │
│ BTC_STR       │
│ BTC_STRAT     │
│ BTC_SYS       │
│ BTC_VIA       │
│ BTC_VRC       │
│ BTC_VTC       │
│ BTC_XBC       │
│ BTC_XCP       │
│ BTC_XEM       │
│ BTC_XMR       │
│ BTC_XPM       │
│ BTC_XRP       │
│ BTC_XVC       │
│ BTC_ZEC       │
│ BTC_ZRX       │
│ ETH_BCH       │
│ ETH_CVC       │
│ ETH_ETC       │
│ ETH_GAS       │
│ ETH_GNO       │
│ ETH_GNT       │
│ ETH_LSK       │
│ ETH_OMG       │
│ ETH_REP       │
│ ETH_STEEM     │
│ ETH_ZEC       │
│ ETH_ZRX       │
│ USDT_BCH      │
│ USDT_BTC      │
│ USDT_DASH     │
│ USDT_ETC      │
│ USDT_ETH      │
│ USDT_LTC      │
│ USDT_NXT      │
│ USDT_REP      │
│ USDT_STR      │
│ USDT_XMR      │
│ USDT_XRP      │
│ USDT_ZEC      │
│ XMR_BCN       │
│ XMR_BLK       │
│ XMR_BTCD      │
│ XMR_DASH      │
│ XMR_LTC       │
│ XMR_MAID      │
│ XMR_NXT       │
│ XMR_ZEC       │
└───────────────┘
```
