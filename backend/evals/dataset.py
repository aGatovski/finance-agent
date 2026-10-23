import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langsmith import Client

from src.config import settings

client = Client(api_key=settings.langsmith_api_key)

# Define the examples for the dataset based on your list
examples = [
    {
        "inputs": {"question": "What are the ways you can buy insurance?"},
        "outputs": {
            "answer": "You can buy insurance traditionally in person at an insurance office, or online via a website or mobile app provided by insurance companies or brokers.",
            "source": "08-insurance.md",
            "chunk_id": 399
        },
    },
    {
        "inputs": {"question": "What entity records dematerialized securities in Bulgaria?"},
        "outputs": {
            "answer": "The Central Depository AD",
            "source": "05-investing.md",
            "chunk_id": 451
        },
    },
    {
        "inputs": {"question": "What costs are typically included in general tourist/mountain insurance coverages in Bulgaria?"},
        "outputs": {
            "answer": "Emergency medical care due to accident, rescue operation, assistance in case of an accident, and primary medical care in the mountains.",
            "source": "travel_finance_bg.md",
            "chunk_id": 158
        },
    },
    {
        "inputs": {"question": "What are some ways to speed up the process of building up personal funds for a home purchase?"},
        "outputs": {
            "answer": "To speed up the process, you can consider ways to increase your income through additional work commitments, selling assets, or seeking help from family.",
            "source": "buying_home_bg.md",
            "chunk_id": 143
        },
    },
    {
        "inputs": {"question": "What are the main coverages typically included in medical insurance policies?"},
        "outputs": {
            "answer": "The main coverages include outpatient and inpatient treatment.",
            "source": "health_risks_finances_bg.md",
            "chunk_id": 132
        },
    },
    {
        "inputs": {"question": "What information can you find on a credit report when filling out a debt log?"},
        "outputs": {
            "answer": "A credit report provides your monthly payment amounts, the balance you still owe, whether you are up to date or more than 30 days late, and your status as an owner, co-signer, or authorized user.",
            "source": "cfpb-debt-log.md",
            "chunk_id": 78
        },
    },
    {
        "inputs": {"question": "What is the difference in goal between directly purchasing a home to live in and investing in real estate?"},
        "outputs": {
            "answer": "The goal of investing in real estate is generating returns through rental income and possibly increasing the value of the asset over time, whereas a personal residential property is intended for private use, provides housing security and comfort, and typically does not generate regular financial returns.",
            "source": "05-investing.md",
            "chunk_id": 448
        },
    },
    {
        "inputs": {"question": "How do I calculate my weekly savings target?"},
        "outputs": {
            "answer": "Divide the amount of money you want to save by the number of weeks you have to save it.",
            "source": "cfpb-savings-plan.md",
            "chunk_id": 59
        },
    },
    {
        "inputs": {"question": "Where can I find the specific conditions and deadlines for filing a compensation claim?"},
        "outputs": {
            "answer": "The specific conditions and deadlines are stated in the general terms of the policy.",
            "source": "08-insurance.md",
            "chunk_id": 418
        },
    },
    {
        "inputs": {"question": "What factors influence the funds accumulated in an individual account under a Supplementary Mandatory Pension Insurance?"},
        "outputs": {
            "answer": "The funds are influenced by the number of contributions, the length of the insurance period, the income from investments, and the amount of fees and deductions collected for the respective fund.",
            "source": "06-retirement.md",
            "chunk_id": 328
        },
    },
    {
        "inputs": {"question": "What are the three steps for planning for life events and large purchases?"},
        "outputs": {
            "answer": "1. Brainstorm a list of expenses and when they're likely to happen. 2. Estimate the costs of these expenses. 3. Identify potential ways to pay for the expenses.",
            "source": "cfpb-saving-for-events-and-purchases.md",
            "chunk_id": 56
        },
    },
    {
        "inputs": {"question": "What is the reflection period for mortgage and housing loans after receiving a draft contract?"},
        "outputs": {
            "answer": "The reflection period is explicitly stated and cannot be shorter than 14 days.",
            "source": "09-consumer-protection.md",
            "chunk_id": 266
        },
    },
    {
        "inputs": {"question": "What is the primary pro of paying off the debt with the highest interest rate first?"},
        "outputs": {
            "answer": "By paying off the debts that charge you the highest interest and fees first, you save money overall.",
            "source": "cfpb-debt-action-plan.md",
            "chunk_id": 17
        },
    },
    {
        "inputs": {"question": "What are the two basic strategies for applying extra money to pay down your debt?"},
        "outputs": {
            "answer": "You can either pay your debts from smallest to largest or focus on repaying the ones with the highest interest rate first.",
            "source": "cfpb-debt-action-plan.md",
            "chunk_id": 15
        },
    },
    {
        "inputs": {"question": "What should I do after I've used up my emergency savings?"},
        "outputs": {
            "answer": "It is time to replenish your emergency savings by determining how much you want to save and by when, calculating the weekly or monthly amount needed to meet that goal, and starting to save. You may also need to adjust other goals, priorities, or the length and total amount of other saving goals.",
            "source": "cfpb-revising-goals.md",
            "chunk_id": 51
        },
    },
    {
        "inputs": {"question": "What is the ceiling for cash payments set by the Limitation of Cash Payments Act?"},
        "outputs": {
            "answer": "EUR 5,000",
            "source": "03-payments.md",
            "chunk_id": 137
        },
    },
]

# Create the dataset and examples in LangSmith
dataset_name = "Financial Literacy Q&A"
dataset = client.create_dataset(dataset_name=dataset_name)
client.create_examples(
    dataset_id=dataset.id,
    examples=examples
)