# # backend/main.py
# from fastapi import APIRouter, FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# from typing import Dict, List, Optional, Any
# from datetime import datetime, timedelta
# import math
# import calendar

# router = APIRouter()


# class ExtraPayments(BaseModel):
#     monthly: Dict[str, Any] = Field(default_factory=dict)
#     yearly: Dict[str, Any] = Field(default_factory=dict)
#     oneTime: List[Dict[str, Any]] = Field(default_factory=list)

# class LoanRequest(BaseModel):
#     loanAmount: float
#     interestRate: float
#     loanTerm: int
#     startDate: str
#     startMonth: Optional[str] = "Jan"
#     startYear: Optional[int] = 2025
#     extraPayments: Optional[ExtraPayments] = None

# class PaymentScheduleItem(BaseModel):
#     paymentNumber: int
#     paymentDate: str
#     beginningBalance: float
#     scheduledPayment: float
#     extraPayment: float
#     totalPayment: float
#     principal: float
#     interest: float
#     endingBalance: float
#     cumulativeInterest: float

# class YearlyScheduleItem(BaseModel):
#     year: int
#     beginningBalance: float
#     totalPayments: float
#     totalPrincipal: float
#     totalInterest: float
#     totalExtraPayments: float
#     endingBalance: float
#     cumulativeInterest: float

# class AmortizationResult(BaseModel):
#     monthlyPayment: float
#     totalPayments: float
#     totalInterest: float
#     payoffDate: str
#     schedule: List[PaymentScheduleItem]
#     yearlySchedule: List[YearlyScheduleItem]
#     payoffDate: str
#     schedule: List[PaymentScheduleItem]

# def calculate_monthly_payment(loan_amount: float, annual_rate: float, term_years: int) -> float:
#     """Calculate monthly payment using standard amortization formula"""
#     if annual_rate == 0:
#         return loan_amount / (term_years * 12)
    
#     monthly_rate = annual_rate / 100 / 12
#     num_payments = term_years * 12
    
#     monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
#                      ((1 + monthly_rate) ** num_payments - 1)
    
#     return monthly_payment

# def get_month_number(month_name: str) -> int:
#     """Convert month name to number"""
#     months = {
#         'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
#         'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
#     }
#     return months.get(month_name, 1)

# def calculate_extra_payment(payment_date: datetime, extra_payments: ExtraPayments, payment_number: int) -> float:
#     """Calculate extra payment for a given payment date"""
#     if not extra_payments:
#         return 0.0
    
#     total_extra = 0.0
#     current_year = payment_date.year
#     current_month = payment_date.month
    
#     # Monthly extra payments
#     if extra_payments.monthly and extra_payments.monthly.get('amount', 0) > 0:
#         from_month = get_month_number(extra_payments.monthly.get('fromMonth', 'Jan'))
#         from_year = extra_payments.monthly.get('fromYear', current_year)
        
#         if (current_year > from_year or 
#             (current_year == from_year and current_month >= from_month)):
#             total_extra += extra_payments.monthly.get('amount', 0)
    
#     # Yearly extra payments (applied once per year in specified month)
#     if extra_payments.yearly and extra_payments.yearly.get('amount', 0) > 0:
#         yearly_month = get_month_number(extra_payments.yearly.get('fromMonth', 'Jan'))
#         yearly_from_year = extra_payments.yearly.get('fromYear', current_year)
        
#         if (current_year >= yearly_from_year and current_month == yearly_month):
#             total_extra += extra_payments.yearly.get('amount', 0)
    
#     # One-time extra payments
#     if extra_payments.oneTime:
#         for one_time in extra_payments.oneTime:
#             if (one_time.get('amount', 0) > 0 and
#                 one_time.get('year', 0) == current_year and
#                 get_month_number(one_time.get('month', 'Jan')) == current_month):
#                 total_extra += one_time.get('amount', 0)
    
#     return total_extra

# def generate_yearly_schedule(monthly_schedule: List[PaymentScheduleItem]) -> List[YearlyScheduleItem]:
#     """Generate yearly schedule from monthly schedule"""
#     yearly_data = {}
    
#     for payment in monthly_schedule:
#         payment_date = datetime.strptime(payment.paymentDate, "%Y-%m-%d")
#         year = payment_date.year
        
#         if year not in yearly_data:
#             yearly_data[year] = {
#                 'year': year,
#                 'beginningBalance': payment.beginningBalance,
#                 'totalPayments': 0.0,
#                 'totalPrincipal': 0.0,
#                 'totalInterest': 0.0,
#                 'totalExtraPayments': 0.0,
#                 'endingBalance': payment.endingBalance,
#                 'cumulativeInterest': payment.cumulativeInterest
#             }
        
#         yearly_data[year]['totalPayments'] += payment.totalPayment
#         yearly_data[year]['totalPrincipal'] += payment.principal
#         yearly_data[year]['totalInterest'] += payment.interest
#         yearly_data[year]['totalExtraPayments'] += payment.extraPayment
#         yearly_data[year]['endingBalance'] = payment.endingBalance
#         yearly_data[year]['cumulativeInterest'] = payment.cumulativeInterest
    
#     # Convert to list and sort by year
#     yearly_schedule = []
#     for year in sorted(yearly_data.keys()):
#         yearly_schedule.append(YearlyScheduleItem(**yearly_data[year]))
    
#     return yearly_schedule

# def generate_amortization_schedule(
#     loan_amount: float,
#     annual_rate: float,
#     term_years: int,
#     start_date: str,
#     start_month: str,
#     start_year: int,
#     extra_payments: ExtraPayments
# ) -> AmortizationResult:
#     """Generate complete amortization schedule with extra payments"""
    
#     monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, term_years)
#     monthly_rate = annual_rate / 100 / 12
    
#     schedule = []
#     current_balance = loan_amount
#     cumulative_interest = 0.0
#     payment_number = 1
    
#     # Use start_month and start_year for initial date
#     start_month_num = get_month_number(start_month)
#     current_date = datetime(start_year, start_month_num, 1)
    
#     while current_balance > 0.01 and payment_number <= term_years * 12 * 2:  # Safety limit
#         # Calculate interest for this payment
#         interest_payment = current_balance * monthly_rate
        
#         # Calculate principal payment
#         principal_payment = min(monthly_payment - interest_payment, current_balance)
        
#         # Add extra payment if specified
#         extra_payment = calculate_extra_payment(current_date, extra_payments, payment_number)
#         if extra_payment > 0:
#             principal_payment += min(extra_payment, current_balance - principal_payment)
        
#         # Ensure we don't overpay
#         if principal_payment > current_balance:
#             principal_payment = current_balance
        
#         total_payment = interest_payment + principal_payment
#         new_balance = current_balance - principal_payment
#         cumulative_interest += interest_payment
        
#         # Create schedule item
#         schedule_item = PaymentScheduleItem(
#             paymentNumber=payment_number,
#             paymentDate=current_date.strftime("%Y-%m-%d"),
#             beginningBalance=current_balance,
#             scheduledPayment=monthly_payment,
#             extraPayment=extra_payment,
#             totalPayment=total_payment,
#             principal=principal_payment,
#             interest=interest_payment,
#             endingBalance=max(0, new_balance),
#             cumulativeInterest=cumulative_interest
#         )
        
#         schedule.append(schedule_item)
        
#         # Update for next iteration
#         current_balance = new_balance
#         payment_number += 1
        
#         # Move to next month
#         if current_date.month == 12:
#             current_date = current_date.replace(year=current_date.year + 1, month=1)
#         else:
#             current_date = current_date.replace(month=current_date.month + 1)
        
#         # Break if balance is essentially zero
#         if current_balance < 0.01:
#             break
    
#     # Generate yearly schedule
#     yearly_schedule = generate_yearly_schedule(schedule)
    
#     # Calculate totals
#     total_payments = sum(item.totalPayment for item in schedule)
#     total_interest = sum(item.interest for item in schedule)
#     payoff_date = schedule[-1].paymentDate if schedule else start_date
    
#     return AmortizationResult(
#         monthlyPayment=monthly_payment,
#         totalPayments=total_payments,
#         totalInterest=total_interest,
#         payoffDate=payoff_date,
#         schedule=schedule,
#         yearlySchedule=yearly_schedule
#     )

#     # @router.get("/")
#     # async def root():
#     #     return {"message": "Amortization Calculator API"}

# @router.post("/amortize-calculator", response_model=AmortizationResult)
# async def calculate_amortization(request: LoanRequest):
#     """Calculate amortization schedule based on loan parameters"""
    
#     try:
#         print(f"Received request: {request}")  # Debug logging
        
#         # Validate inputs
#         if request.loanAmount <= 0:
#             raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
#         if request.interestRate < 0:
#             raise HTTPException(status_code=400, detail="Interest rate cannot be negative")
        
#         if request.loanTerm <= 0:
#             raise HTTPException(status_code=400, detail="Loan term must be positive")
        
#         # Validate date format
#         try:
#             if request.startDate:
#                 datetime.strptime(request.startDate, "%Y-%m-%d")
#         except ValueError:
#             raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
#         # Generate amortization schedule
#         result = generate_amortization_schedule(
#             loan_amount=request.loanAmount,
#             annual_rate=request.interestRate,
#             term_years=request.loanTerm,
#             start_date=request.startDate,
#             start_month=request.startMonth or "Jan",
#             start_year=request.startYear or 2025,
#             extra_payments=request.extraPayments or ExtraPayments()
#         )
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error: {str(e)}")  # Debug logging
#         raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# backend/main.py
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math
import calendar

router =APIRouter()


class ExtraPaymentDetails(BaseModel):
    amount: float = 0
    fromMonth: str = "Jan"
    fromYear: int = 2025

class OneTimePayment(BaseModel):
    amount: float = 0
    month: str = "Jan"
    year: int = 2025

class ExtraPayments(BaseModel):
    monthly: ExtraPaymentDetails = ExtraPaymentDetails()
    yearly: ExtraPaymentDetails = ExtraPaymentDetails()
    oneTime: List[OneTimePayment] = []

class LoanRequest(BaseModel):
    loanAmount: float
    interestRate: float
    loanTerm: int
    startDate: str
    startMonth: Optional[str] = "Jan"
    startYear: Optional[int] = 2025
    extraPayments: Optional[ExtraPayments] = None

class PaymentScheduleItem(BaseModel):
    paymentNumber: int
    paymentDate: str
    beginningBalance: float
    scheduledPayment: float
    extraPayment: float
    totalPayment: float
    principal: float
    interest: float
    endingBalance: float
    cumulativeInterest: float

class YearlyScheduleItem(BaseModel):
    year: int
    beginningBalance: float
    totalPayments: float
    totalPrincipal: float
    totalInterest: float
    totalExtraPayments: float
    endingBalance: float
    cumulativeInterest: float

class AmortizationResult(BaseModel):
    monthlyPayment: float
    totalPayments: float
    totalInterest: float
    payoffDate: str
    schedule: List[PaymentScheduleItem]
    yearlySchedule: List[YearlyScheduleItem]
    payoffDate: str
    schedule: List[PaymentScheduleItem]

def calculate_monthly_payment(loan_amount: float, annual_rate: float, term_years: int) -> float:
    """Calculate monthly payment using standard amortization formula"""
    if annual_rate == 0:
        return loan_amount / (term_years * 12)
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = term_years * 12
    
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                     ((1 + monthly_rate) ** num_payments - 1)
    
    return monthly_payment

def get_month_number(month_name: str) -> int:
    """Convert month name to number"""
    months = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    return months.get(month_name, 1)

def calculate_extra_payment(payment_date: datetime, extra_payments: ExtraPayments, payment_number: int) -> float:
    """Calculate extra payment for a given payment date"""
    if not extra_payments:
        return 0.0
    
    total_extra = 0.0
    current_year = payment_date.year
    current_month = payment_date.month
    
    print(f"Calculating extra payment for date: {payment_date}, payment #{payment_number}")
    
    # Monthly extra payments
    if extra_payments.monthly and extra_payments.monthly.amount > 0:
        from_month = get_month_number(extra_payments.monthly.fromMonth)
        from_year = extra_payments.monthly.fromYear
        
        print(f"Monthly extra: ${extra_payments.monthly.amount} from {extra_payments.monthly.fromMonth} {from_year}")
        
        if (current_year > from_year or 
            (current_year == from_year and current_month >= from_month)):
            total_extra += extra_payments.monthly.amount
            print(f"Applied monthly extra: ${extra_payments.monthly.amount}")
    
    # Yearly extra payments (applied once per year in specified month)
    if extra_payments.yearly and extra_payments.yearly.amount > 0:
        yearly_month = get_month_number(extra_payments.yearly.fromMonth)
        yearly_from_year = extra_payments.yearly.fromYear
        
        print(f"Yearly extra: ${extra_payments.yearly.amount} in {extra_payments.yearly.fromMonth} from {yearly_from_year}")
        
        if (current_year >= yearly_from_year and current_month == yearly_month):
            total_extra += extra_payments.yearly.amount
            print(f"Applied yearly extra: ${extra_payments.yearly.amount}")
    
    # One-time extra payments
    if extra_payments.oneTime:
        for one_time in extra_payments.oneTime:
            if (one_time.amount > 0 and
                one_time.year == current_year and
                get_month_number(one_time.month) == current_month):
                total_extra += one_time.amount
                print(f"Applied one-time extra: ${one_time.amount} for {one_time.month} {one_time.year}")
    
    print(f"Total extra payment: ${total_extra}")
    return total_extra

def generate_yearly_schedule(monthly_schedule: List[PaymentScheduleItem]) -> List[YearlyScheduleItem]:
    """Generate yearly schedule from monthly schedule"""
    yearly_data = {}
    
    for payment in monthly_schedule:
        payment_date = datetime.strptime(payment.paymentDate, "%Y-%m-%d")
        year = payment_date.year
        
        if year not in yearly_data:
            yearly_data[year] = {
                'year': year,
                'beginningBalance': payment.beginningBalance,
                'totalPayments': 0.0,
                'totalPrincipal': 0.0,
                'totalInterest': 0.0,
                'totalExtraPayments': 0.0,
                'endingBalance': payment.endingBalance,
                'cumulativeInterest': payment.cumulativeInterest
            }
        
        yearly_data[year]['totalPayments'] += payment.totalPayment
        yearly_data[year]['totalPrincipal'] += payment.principal
        yearly_data[year]['totalInterest'] += payment.interest
        yearly_data[year]['totalExtraPayments'] += payment.extraPayment
        yearly_data[year]['endingBalance'] = payment.endingBalance
        yearly_data[year]['cumulativeInterest'] = payment.cumulativeInterest
    
    # Convert to list and sort by year
    yearly_schedule = []
    for year in sorted(yearly_data.keys()):
        yearly_schedule.append(YearlyScheduleItem(**yearly_data[year]))
    
    return yearly_schedule

def generate_amortization_schedule(
    loan_amount: float,
    annual_rate: float,
    term_years: int,
    start_date: str,
    start_month: str,
    start_year: int,
    extra_payments: ExtraPayments
) -> AmortizationResult:
    """Generate complete amortization schedule with extra payments"""
    
    monthly_payment = calculate_monthly_payment(loan_amount, annual_rate, term_years)
    monthly_rate = annual_rate / 100 / 12
    
    schedule = []
    current_balance = loan_amount
    cumulative_interest = 0.0
    payment_number = 1
    
    # Use start_month and start_year for initial date
    start_month_num = get_month_number(start_month)
    current_date = datetime(start_year, start_month_num, 1)
    
    while current_balance > 0.01 and payment_number <= term_years * 12 * 2:  # Safety limit
        # Calculate interest for this payment
        interest_payment = current_balance * monthly_rate
        
        # Calculate principal payment
        principal_payment = min(monthly_payment - interest_payment, current_balance)
        
        # Add extra payment if specified
        extra_payment = calculate_extra_payment(current_date, extra_payments, payment_number)
        
        # Apply extra payment to principal
        if extra_payment > 0:
            # Ensure we don't pay more than the remaining balance
            available_for_extra = max(0, current_balance - principal_payment)
            actual_extra = min(extra_payment, available_for_extra)
            principal_payment += actual_extra
            extra_payment = actual_extra  # Update to reflect actual amount applied
        
        # Ensure total principal doesn't exceed current balance
        if principal_payment > current_balance:
            principal_payment = current_balance
        
        total_payment = interest_payment + principal_payment
        new_balance = current_balance - principal_payment
        cumulative_interest += interest_payment
        
        # Create schedule item
        schedule_item = PaymentScheduleItem(
            paymentNumber=payment_number,
            paymentDate=current_date.strftime("%Y-%m-%d"),
            beginningBalance=current_balance,
            scheduledPayment=monthly_payment,
            extraPayment=extra_payment,
            totalPayment=total_payment,
            principal=principal_payment,
            interest=interest_payment,
            endingBalance=max(0, new_balance),
            cumulativeInterest=cumulative_interest
        )
        
        schedule.append(schedule_item)
        
        # Update for next iteration
        current_balance = new_balance
        payment_number += 1
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
        
        # Break if balance is essentially zero
        if current_balance < 0.01:
            break
    
    # Generate yearly schedule
    yearly_schedule = generate_yearly_schedule(schedule)
    
    # Calculate totals
    total_payments = sum(item.totalPayment for item in schedule)
    total_interest = sum(item.interest for item in schedule)
    payoff_date = schedule[-1].paymentDate if schedule else start_date
    
    return AmortizationResult(
        monthlyPayment=monthly_payment,
        totalPayments=total_payments,
        totalInterest=total_interest,
        payoffDate=payoff_date,
        schedule=schedule,
        yearlySchedule=yearly_schedule
    )



@router.post("/amortize-calculate", response_model=AmortizationResult)
async def calculate_amortization(request: LoanRequest):
    """Calculate amortization schedule based on loan parameters"""
    
    try:
        print(f"Received request: {request}")  # Debug logging
        print(f"Extra payments: {request.extraPayments}")  # Debug extra payments
        
        # Validate inputs
        if request.loanAmount <= 0:
            raise HTTPException(status_code=400, detail="Loan amount must be positive")
        
        if request.interestRate < 0:
            raise HTTPException(status_code=400, detail="Interest rate cannot be negative")
        
        if request.loanTerm <= 0:
            raise HTTPException(status_code=400, detail="Loan term must be positive")
        
        # Validate date format if provided
        if request.startDate:
            try:
                datetime.strptime(request.startDate, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Generate amortization schedule
        result = generate_amortization_schedule(
            loan_amount=request.loanAmount,
            annual_rate=request.interestRate,
            term_years=request.loanTerm,
            start_date=request.startDate or f"{request.startYear}-{get_month_number(request.startMonth):02d}-01",
            start_month=request.startMonth or "Jan",
            start_year=request.startYear or 2025,
            extra_payments=request.extraPayments or ExtraPayments()
        )
        
        print(f"Generated {len(result.schedule)} payments with total interest: ${result.totalInterest:.2f}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

