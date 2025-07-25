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

def calculate_mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate monthly mortgage payment using the standard formula"""
    if annual_rate == 0:
        return principal / (years * 12)
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                     ((1 + monthly_rate) ** num_payments - 1)
    
    return monthly_payment

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

@router.get("/")
async def root():
    return {"message": "Mortgage Calculator API"}

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
        
        # Calculate payoff date
        payoff_date = calculate_payoff_date(inputs.startMonth, inputs.startYear, inputs.loanTerm)
        
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
            payoffDate=payoff_date
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

