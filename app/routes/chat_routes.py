from fastapi import APIRouter, HTTPException
from collections import defaultdict
from app.models import ChatInput
from app.database import chat_collection
from openai import OpenAI
import os
import requests
from bs4 import BeautifulSoup
import asyncio

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
message_histories = defaultdict(list)

SYSTEM_PROMPT = (
    "You are a U.S. financial assistant that answers only questions related to loans, mortgages, and housing finance. "
    "You provide accurate, practical information specifically for users in the United States.\n\n"
    "Always format detailed responses in lists or tables where applicable.\n\n"
    "You are allowed to fetch and present the latest available mortgage rates using online sources when the user asks about current rates.\n\n"

    "  U.S. Home Loans:\n"
    "- Conventional loans\n"
    "- FHA loans (Federal Housing Administration)\n"
    "- VA loans (for veterans)\n"
    "- USDA loans (for rural housing)\n"
    "- Jumbo loans\n"
    "- Fixed-rate vs Adjustable-rate mortgages (ARM)\n"
    "- Pre-approval, down payments, escrow, closing costs\n\n"

    "  Mortgage Finance Topics:\n"
    "- Loan-to-Value (LTV) ratio\n"
    "- Debt-to-Income (DTI) ratio\n"
    "- Mortgage insurance (PMI, MIP)\n"
    "- Interest rates and amortization\n"
    "- Credit score impact on loan approval\n"
    "- Refinance options\n\n"

    "  Personal Loans (U.S.):\n"
    "- Secured vs unsecured loans\n"
    "- Bank, credit union, and online lenders\n"
    "- APR, fees, repayment terms\n"
    "- Loan consolidation\n\n"

    "  U.S. Regulations and Assistance:\n"
    "- Fannie Mae & Freddie Mac\n"
    "- CFPB guidelines\n"
    "- HUD programs\n"
    "- First-time homebuyer assistance\n"
    "- Loan modification and foreclosure help\n\n"

    "You are allowed to look up or simulate real-time values when relevant to U.S. housing finance or loan queries. "
    "Politely refuse to answer any question that is not about U.S. loans, mortgages, or housing finance."
)

def get_mortgage_rates():
    url = "https://www.mortgagenewsdaily.com/mortgage-rates"
    response = requests.get(url)
    print("Fetched URL status:", response.status_code)

    soup = BeautifulSoup(response.content, "html.parser")
    print("Soup created")

    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables")
    for i, table in enumerate(tables):
        print(f"Table {i} class: {table.get('class')}")

    # Updated selector based on class
    rates = {}
    for table in soup.find_all("table", class_="mtg-rates"):
        rows = table.find_all("tr")
        print(f"Found {len(rows)} rows in table.mtg-rates")

        for i, row in enumerate(rows[1:], start=1):
            cols = row.find_all("td")
            print(f"Row {i}: {len(cols)} columns")

            if len(cols) >= 2:
                rate_type = cols[0].text.strip()
                rate_value = cols[1].text.strip()
                print(f"Rate Type: {rate_type}, Rate Value: {rate_value}")
                rates[rate_type] = rate_value

    print("Final rates dictionary:", rates)
    return rates

def get_fannie_mae_summary():
    url = "https://selling-guide.fanniemae.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"


def get_freddie_mac_summary():
    url = "https://guide.freddiemac.com/app/guide/browse"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"


def get_hud_fha_summary():
    url = "https://www.hud.gov/hud-partners/single-family-fha-resource-center"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
        return "\n\n".join(text_blocks[:2]) if text_blocks else "No content extracted."
    except Exception as e:
        return f"Failed to fetch: {str(e)}"




@router.post("/chat")
async def chat(input: ChatInput):
    try:
        chat_collection.insert_one(input.dict())
        user_email = input.email
        user_message = input.message.strip().lower()

        if not message_histories[user_email]:
            message_histories[user_email].append({"role": "system", "content": SYSTEM_PROMPT})

        message_histories[user_email].append({"role": "user", "content": user_message})

        # Check for mortgage keyword
        if any(kw in user_message for kw in ["mortgage rates", "home loan rates", "current rates", "rates"]):
            try:
                rates = get_mortgage_rates()
                formatted_rates = "\n".join([f"{k}: {v}" for k, v in rates.items()])
                bot_reply = (
                    f"Here are the current mortgage rates:\n{formatted_rates}\n\n"
                    "Please reach out to us to get a personalized quote. "
                    "Let me know if you would like to connect with a Loan Officer."
                )
            except Exception:
                bot_reply = "Sorry, I couldn't fetch the latest mortgage rates right now."
        elif any(kw in user_message for kw in ["fannie mae", "freddie mac", "hud", "government loan"]):
            summaries = {
                "Fannie Mae": get_fannie_mae_summary(),
                "Freddie Mac": get_freddie_mac_summary(),
                "HUD FHA": get_hud_fha_summary()
            }
            bot_reply = "Here is official information on U.S. housing finance programs:\n\n"
            for name, summary in summaries.items():
                bot_reply += f"**{name}**\n{summary}\n\n"


        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=message_histories[user_email],
                temperature=0.7,
                max_tokens=300
            )
            bot_reply = response.choices[0].message.content.strip()
        replacements = {
            "speak with a lender": "please reach out to us",
            "talk to a lender": "please reach out to us",
            "consult with a lender": "please reach out to us",
            "contact a lender": "please reach out to us",
            "talk to your bank": "please reach out to us",
            "consult your bank": "please reach out to us",
            "speak to your bank": "please reach out to us",
            "consult with your lender": "please reach out to us",
            "reach out to a lender": "please reach out to us",
        }

        for phrase, replacement in replacements.items():
            bot_reply = bot_reply.replace(phrase, replacement)

        message_histories[user_email].append({"role": "assistant", "content": bot_reply})

        chat_collection.insert_one({
            "email": input.email,
            "message": bot_reply,
            "sender": "bot"
        })

        return {"reply": bot_reply}

    except asyncio.CancelledError:
        print("Request was cancelled.")
        raise HTTPException(status_code=499, detail="Request cancelled by client")
    except Exception as e:
        print("Unexpected error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
        

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))