# # main.py
# from fastapi import APIRouter, FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# import math
# from typing import Literal

# router = APIRouter()

# @router.get("/")
# async def root():
#     return {"message": "Amortization Calculator API"}

# class MortgageInputs(BaseModel):
#     homePrice: float
#     downPayment: float
#     downPaymentType: Literal['dollar', 'percent']
#     loanTerm: int
#     interestRate: float
#     startMonth: int
#     startYear: int
#     includeTaxesCosts: bool = False
#     propertyTax: float = 0
#     propertyTaxType: Literal['dollar', 'percent'] = 'percent'
#     homeInsurance: float = 0
#     homeInsuranceType: Literal['dollar', 'percent'] = 'percent'
#     pmiInsurance: float = 0
#     pmiInsuranceType: Literal['dollar', 'percent'] = 'percent'
#     hoaFee: float = 0
#     hoaFeeType: Literal['dollar', 'percent'] = 'percent'
#     otherCosts: float = 0
#     otherCostsType: Literal['dollar', 'percent'] = 'percent'
#     # Additional options
#     propertyTaxIncrease: float = 0
#     homeInsuranceIncrease: float = 0
#     hoaFeeIncrease: float = 0
#     otherCostsIncrease: float = 0
#     extraMonthlyPay: float = 0
#     extraMonthlyPayMonth: int = 1
#     extraMonthlyPayYear: int = 2025
#     extraYearlyPay: float = 0
#     extraYearlyPayMonth: int = 1
#     extraYearlyPayYear: int = 2025
#     extraOneTimePay: float = 0  
#     extraOneTimePayMonth: int = 1
#     extraOneTimePayYear: int = 2025

# class MortgageResults(BaseModel):
#     monthlyPayment: float
#     totalMonthlyPayment: float
#     totalInterest: float
#     totalPayments: float
#     loanAmount: float
#     downPaymentAmount: float
#     propertyTaxMonthly: float
#     homeInsuranceMonthly: float
#     pmiMonthly: float
#     hoaMonthly: float
#     otherCostsMonthly: float
#     payoffDate: str

# def calculate_mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
#     """Calculate monthly mortgage payment using the standard formula"""
#     if annual_rate == 0:
#         return principal / (years * 12)
    
#     monthly_rate = annual_rate / 100 / 12
#     num_payments = years * 12
    
#     monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
#                      ((1 + monthly_rate) ** num_payments - 1)
    
#     return monthly_payment

# def calculate_payoff_date(start_month: int, start_year: int, loan_term_years: int) -> str:
#     """Calculate the mortgage payoff date"""
#     try:
#         start_date = datetime(start_year, start_month, 1)
#         payoff_date = start_date + timedelta(days=loan_term_years * 365.25)
        
#         months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
#                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
#         return f"{months[payoff_date.month - 1]}. {payoff_date.year}"
#     except ValueError:
#         return "Invalid Date"



# @router.post("/calculate", response_model=MortgageResults)
# async def calculate_mortgage(inputs: MortgageInputs):
#     try:
#         # Calculate down payment amount
#         if inputs.downPaymentType == 'percent':
#             down_payment_amount = inputs.homePrice * (inputs.downPayment / 100)
#         else:
#             down_payment_amount = inputs.downPayment
        
#         # Calculate loan amount
#         loan_amount = inputs.homePrice - down_payment_amount
        
#         # Calculate monthly mortgage payment (Principal & Interest)
#         if loan_amount <= 0:
#             monthly_payment = 0
#             total_interest = 0
#             total_payments = 0
#         else:
#             monthly_payment = calculate_mortgage_payment(loan_amount, inputs.interestRate, inputs.loanTerm)
#             total_payments = monthly_payment * inputs.loanTerm * 12
#             total_interest = total_payments - loan_amount
        
#         # Calculate monthly taxes and costs
#         property_tax_monthly = 0
#         home_insurance_monthly = 0
#         pmi_monthly = 0
#         hoa_monthly = 0
#         other_costs_monthly = 0
        
#         if inputs.includeTaxesCosts:
#             # Property Tax
#             if inputs.propertyTaxType == 'percent':
#                 property_tax_monthly = (inputs.homePrice * inputs.propertyTax / 100) / 12
#             else:
#                 property_tax_monthly = inputs.propertyTax / 12
            
#             # Home Insurance
#             if inputs.homeInsuranceType == 'percent':
#                 home_insurance_monthly = (inputs.homePrice * inputs.homeInsurance / 100) / 12
#             else:
#                 home_insurance_monthly = inputs.homeInsurance / 12
            
#             # PMI Insurance
#             if inputs.pmiInsuranceType == 'percent':
#                 pmi_monthly = (loan_amount * inputs.pmiInsurance / 100) / 12
#             else:
#                 pmi_monthly = inputs.pmiInsurance
            
#             # HOA Fee
#             if inputs.hoaFeeType == 'percent':
#                 hoa_monthly = (inputs.homePrice * inputs.hoaFee / 100) / 12
#             else:
#                 hoa_monthly = inputs.hoaFee
            
#             # Other Costs
#             if inputs.otherCostsType == 'percent':
#                 other_costs_monthly = (inputs.homePrice * inputs.otherCosts / 100) / 12
#             else:
#                 other_costs_monthly = inputs.otherCosts / 12
        
#         # Calculate total monthly payment
#         total_monthly_payment = (monthly_payment + property_tax_monthly + 
#                                home_insurance_monthly + pmi_monthly + 
#                                hoa_monthly + other_costs_monthly)
        
#         # Calculate payoff date
#         payoff_date = calculate_payoff_date(inputs.startMonth, inputs.startYear, inputs.loanTerm)
        
#         return MortgageResults(
#             monthlyPayment=round(monthly_payment, 2),
#             totalMonthlyPayment=round(total_monthly_payment, 2),
#             totalInterest=round(total_interest, 2),
#             totalPayments=round(total_payments, 2),
#             loanAmount=round(loan_amount, 2),
#             downPaymentAmount=round(down_payment_amount, 2),
#             propertyTaxMonthly=round(property_tax_monthly, 2),
#             homeInsuranceMonthly=round(home_insurance_monthly, 2),
#             pmiMonthly=round(pmi_monthly, 2),
#             hoaMonthly=round(hoa_monthly, 2),
#             otherCostsMonthly=round(other_costs_monthly, 2),
#             payoffDate=payoff_date
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

def calculate_payoff_date(start_month: int, start_year: int, loan_term_years: int) -> str:
    """Calculate the mortgage payoff date"""
    try:
        start_date = datetime(start_year, start_month, 1)
        payoff_date = start_date + timedelta(days=loan_term_years * 365.25)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return f"{months[payoff_date.month - 1]}. {payoff_date.year}"
    except ValueError:
        return "Invalid Date"
    # main.py
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import math
from typing import Literal

router = APIRouter()



class MortgageInputs(BaseModel):
    homePrice: float
    downPayment: float
    downPaymentType: Literal['dollar', 'percent']
    loanTerm: int
    interestRate: float
    startMonth: int
    startYear: int
    includeTaxesCosts: bool = False
    propertyTax: float = 0
    propertyTaxType: Literal['dollar', 'percent'] = 'percent'
    homeInsurance: float = 0
    homeInsuranceType: Literal['dollar', 'percent'] = 'percent'
    pmiInsurance: float = 0
    pmiInsuranceType: Literal['dollar', 'percent'] = 'percent'
    hoaFee: float = 0
    hoaFeeType: Literal['dollar', 'percent'] = 'percent'
    otherCosts: float = 0
    otherCostsType: Literal['dollar', 'percent'] = 'percent'
    # Additional options
    propertyTaxIncrease: float = 0
    homeInsuranceIncrease: float = 0
    hoaFeeIncrease: float = 0
    otherCostsIncrease: float = 0
    extraMonthlyPay: float = 0
    extraMonthlyPayMonth: int = 1
    extraMonthlyPayYear: int = 2025
    extraYearlyPay: float = 0
    extraYearlyPayMonth: int = 1
    extraYearlyPayYear: int = 2025
    extraOneTimePay: float = 0
    extraOneTimePayMonth: int = 1
    extraOneTimePayYear: int = 2025

class MortgageResults(BaseModel):
    monthlyPayment: float
    totalMonthlyPayment: float
    totalInterest: float
    totalPayments: float
    loanAmount: float
    downPaymentAmount: float
    propertyTaxMonthly: float
    homeInsuranceMonthly: float
    pmiMonthly: float
    hoaMonthly: float
    otherCostsMonthly: float
    payoffDate: str
    totalInterestWithExtras: float = 0
    totalPaymentsWithExtras: float = 0
    payoffDateWithExtras: str = ""
    monthsSaved: int = 0
    interestSaved: float = 0

def calculate_mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate monthly mortgage payment using the standard formula"""
    if annual_rate == 0:
        return principal / (years * 12)
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                     ((1 + monthly_rate) ** num_payments - 1)
    
    return monthly_payment

def calculate_amortization_with_extras(
    principal: float, 
    annual_rate: float, 
    years: int,
    start_month: int,
    start_year: int,
    extra_monthly: float = 0,
    extra_monthly_start_month: int = 1,
    extra_monthly_start_year: int = 2025,
    extra_yearly: float = 0,
    extra_yearly_month: int = 1,
    extra_yearly_year: int = 2025,
    extra_onetime: float = 0,
    extra_onetime_month: int = 1,
    extra_onetime_year: int = 2025
) -> tuple:
    """Calculate mortgage with extra payments"""
    if annual_rate == 0 or principal <= 0:
        return 0, 0, f"{start_year + years}", 0
    
    monthly_rate = annual_rate / 100 / 12
    base_payment = calculate_mortgage_payment(principal, annual_rate, years)
    
    balance = principal
    total_paid = 0
    total_interest = 0
    payment_number = 0
    current_date = datetime(start_year, start_month, 1)
    
    extra_monthly_start = datetime(extra_monthly_start_year, extra_monthly_start_month, 1)
    extra_yearly_date = datetime(extra_yearly_year, extra_yearly_month, 1)
    extra_onetime_date = datetime(extra_onetime_year, extra_onetime_month, 1)
    
    while balance > 0.01 and payment_number < years * 12 * 2:  # Safety limit
        payment_number += 1
        
        # Calculate interest for this month
        interest_payment = balance * monthly_rate
        principal_payment = base_payment - interest_payment
        
        # Calculate extra payments for this month
        extra_this_month = 0
        
        # Extra monthly payment
        if current_date >= extra_monthly_start and extra_monthly > 0:
            extra_this_month += extra_monthly
        
        # Extra yearly payment (if it's the right month and year)
        if (current_date.month == extra_yearly_date.month and 
            current_date.year >= extra_yearly_date.year and 
            extra_yearly > 0):
            extra_this_month += extra_yearly
        
        # Extra one-time payment
        if (current_date.month == extra_onetime_date.month and 
            current_date.year == extra_onetime_date.year and 
            extra_onetime > 0):
            extra_this_month += extra_onetime
        
        # Total payment (principal + extra, but not more than remaining balance)
        total_principal_payment = min(principal_payment + extra_this_month, balance)
        
        # Update balance and totals
        balance -= total_principal_payment
        total_interest += interest_payment
        total_paid += interest_payment + total_principal_payment
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Calculate payoff date
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    payoff_date = f"{months[current_date.month - 1]}. {current_date.year}"
    
    return total_interest, total_paid, payoff_date, payment_number



@router.post("/calculate", response_model=MortgageResults)
async def calculate_mortgage(inputs: MortgageInputs):
    try:
        # Calculate down payment amount
        if inputs.downPaymentType == 'percent':
            down_payment_amount = inputs.homePrice * (inputs.downPayment / 100)
        else:
            down_payment_amount = inputs.downPayment
        
        # Calculate loan amount
        loan_amount = inputs.homePrice - down_payment_amount
        
        # Calculate monthly mortgage payment (Principal & Interest)
        if loan_amount <= 0:
            monthly_payment = 0
            total_interest = 0
            total_payments = 0
        else:
            monthly_payment = calculate_mortgage_payment(loan_amount, inputs.interestRate, inputs.loanTerm)
            total_payments = monthly_payment * inputs.loanTerm * 12
            total_interest = total_payments - loan_amount
        
        # Calculate monthly taxes and costs
        property_tax_monthly = 0
        home_insurance_monthly = 0
        pmi_monthly = 0
        hoa_monthly = 0
        other_costs_monthly = 0
        
        if inputs.includeTaxesCosts:
            # Property Tax
            if inputs.propertyTaxType == 'percent':
                property_tax_monthly = (inputs.homePrice * inputs.propertyTax / 100) / 12
            else:
                property_tax_monthly = inputs.propertyTax / 12
            
            # Home Insurance
            if inputs.homeInsuranceType == 'percent':
                home_insurance_monthly = (inputs.homePrice * inputs.homeInsurance / 100) / 12
            else:
                home_insurance_monthly = inputs.homeInsurance / 12
            
            # PMI Insurance
            if inputs.pmiInsuranceType == 'percent':
                pmi_monthly = (loan_amount * inputs.pmiInsurance / 100) / 12
            else:
                pmi_monthly = inputs.pmiInsurance
            
            # HOA Fee
            if inputs.hoaFeeType == 'percent':
                hoa_monthly = (inputs.homePrice * inputs.hoaFee / 100) / 12
            else:
                hoa_monthly = inputs.hoaFee
            
            # Other Costs
            if inputs.otherCostsType == 'percent':
                other_costs_monthly = (inputs.homePrice * inputs.otherCosts / 100) / 12
            else:
                other_costs_monthly = inputs.otherCosts / 12
        
        # Calculate total monthly payment
        total_monthly_payment = (monthly_payment + property_tax_monthly + 
                               home_insurance_monthly + pmi_monthly + 
                               hoa_monthly + other_costs_monthly)
        
        # Calculate payoff date (without extra payments)
        payoff_date = calculate_payoff_date(inputs.startMonth, inputs.startYear, inputs.loanTerm)
        
        # Calculate with extra payments if any are specified
        has_extra_payments = (inputs.extraMonthlyPay > 0 or 
                             inputs.extraYearlyPay > 0 or 
                             inputs.extraOneTimePay > 0)
        
        if has_extra_payments and loan_amount > 0:
            (total_interest_with_extras, 
             total_payments_with_extras, 
             payoff_date_with_extras, 
             months_with_extras) = calculate_amortization_with_extras(
                loan_amount,
                inputs.interestRate,
                inputs.loanTerm,
                inputs.startMonth,
                inputs.startYear,
                inputs.extraMonthlyPay,
                inputs.extraMonthlyPayMonth,
                inputs.extraMonthlyPayYear,
                inputs.extraYearlyPay,
                inputs.extraYearlyPayMonth,
                inputs.extraYearlyPayYear,
                inputs.extraOneTimePay,
                inputs.extraOneTimePayMonth,
                inputs.extraOneTimePayYear
            )
            
            months_saved = (inputs.loanTerm * 12) - months_with_extras
            interest_saved = total_interest - total_interest_with_extras
        else:
            total_interest_with_extras = total_interest
            total_payments_with_extras = total_payments + property_tax_monthly * inputs.loanTerm * 12 + home_insurance_monthly * inputs.loanTerm * 12 + (pmi_monthly + hoa_monthly + other_costs_monthly) * inputs.loanTerm * 12
            payoff_date_with_extras = payoff_date
            months_saved = 0
            interest_saved = 0
        
        return MortgageResults(
            monthlyPayment=round(monthly_payment, 2),
            totalMonthlyPayment=round(total_monthly_payment, 2),
            totalInterest=round(total_interest, 2),
            totalPayments=round(total_payments, 2),
            loanAmount=round(loan_amount, 2),
            downPaymentAmount=round(down_payment_amount, 2),
            propertyTaxMonthly=round(property_tax_monthly, 2),
            homeInsuranceMonthly=round(home_insurance_monthly, 2),
            pmiMonthly=round(pmi_monthly, 2),
            hoaMonthly=round(hoa_monthly, 2),
            otherCostsMonthly=round(other_costs_monthly, 2),
            payoffDate=payoff_date,
            totalInterestWithExtras=round(total_interest_with_extras, 2),
            totalPaymentsWithExtras=round(total_payments_with_extras, 2),
            payoffDateWithExtras=payoff_date_with_extras,
            monthsSaved=months_saved,
            interestSaved=round(interest_saved, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

