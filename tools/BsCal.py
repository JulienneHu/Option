import QuantLib as ql
from datetime import datetime

today = ql.Date(datetime.today().day, datetime.today().month, datetime.today().year)
ql.Settings.instance().evaluationDate = today
class BlackScholes:
    def __init__(self):
        self.calendar = ql.NullCalendar()
        self.day_count = ql.Actual365Fixed()

    def blsprice(self, cp_flag, S, X, T, r, v):
        print(f"Input Parameters: cp_flag={cp_flag}, S={S}, X={X}, T={T}, r={r}, v={v}")
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)
        european_option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        volatility = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            ql.BlackVolTermStructureHandle(volatility)
        )
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        price = european_option.NPV()
        print(f"Calculated NPV: {price}")
        return price

    def blsdelta(self, cp_flag, S, X, T, r, v):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)
        european_option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        volatility = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            ql.BlackVolTermStructureHandle(volatility)
        )
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        delta = european_option.delta()
        return delta

    def blsimpv(self, cp_flag, S, X, T, r, C, sigma, tol=1e-6, max_iterations=100):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)
        european_option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        volatility = ql.SimpleQuote(sigma)
        volatility_handle = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(evaluation_date, self.calendar, ql.QuoteHandle(volatility), self.day_count)
        )
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            volatility_handle
        )
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        try:
            implied_vol = european_option.impliedVolatility(C, bsm_process, tol, max_iterations)
        except RuntimeError:
            implied_vol = float('nan')
        return implied_vol
    
   
    def blsgamma(self, S, X, T, r, v):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        payoff = ql.PlainVanillaPayoff(ql.Option.Call, X)  # gamma is same for call/put
        exercise = ql.EuropeanExercise(maturity_date)
        option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        vol = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        rf = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend),
            ql.YieldTermStructureHandle(rf),
            ql.BlackVolTermStructureHandle(vol)
        )
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        return option.gamma()

    def blstheta(self, cp_flag, S, X, T, r, v):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)
        option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        vol = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        rf = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend),
            ql.YieldTermStructureHandle(rf),
            ql.BlackVolTermStructureHandle(vol)
        )
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        return option.theta()

    def blsvega(self, S, X, T, r, v):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        payoff = ql.PlainVanillaPayoff(ql.Option.Call, X)  # vega is same for call/put
        exercise = ql.EuropeanExercise(maturity_date)
        option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        vol = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        rf = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend),
            ql.YieldTermStructureHandle(rf),
            ql.BlackVolTermStructureHandle(vol)
        )
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        return option.vega()

    def blsrho(self, cp_flag, S, X, T, r, v):
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)
        option = ql.VanillaOption(payoff, exercise)
        underlying = ql.SimpleQuote(S)
        vol = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        rf = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)
        process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend),
            ql.YieldTermStructureHandle(rf),
            ql.BlackVolTermStructureHandle(vol)
        )
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))
        return option.rho()

