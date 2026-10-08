import redis
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

@tool
def save_student(
    name: str,
    department: str,
    attendance: float
) -> str:
    """Save or update a student's information."""

    key = f"student:{name.lower()}"

    redis_client.hset(
        key,
        mapping={
            "name": name,
            "department": department,
            "attendance": attendance
        }
    )

    return f"{name}'s information has been saved."

@tool
def get_student_information(name: str) -> str:
    """Get a student's department by name."""

    key = f"student:{name.lower()}"
    student = redis_client.hgetall(key)

    if not student:
        return f"I couldn't find {name} in the student database."

    return (
        f"{student['name']} is from the "
        f"{student['department']} department."
    )

@tool
def get_attendance(name: str) -> str:
    """Get a student's attendance by name."""

    key = f"student:{name.lower()}"
    student = redis_client.hgetall(key)

    if not student:
        return f"I couldn't find {name} in the student database."

    return (
        f"{student['name']}'s attendance is "
        f"{student['attendance']}%."
    )

@tool
def calculator(expression: str) -> str:
    """Perform a mathematical calculation."""
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"

tools = [
    save_student,
    get_student_information,
    get_attendance,
    calculator
]

llm = ChatGroq(
    model="openai/gpt-oss-120b"
)

agent = create_agent(
    llm,
    tools,
    system_prompt=(
        "You are a cute Student Assistant AI Agent. "
        "Whenever the user provides a student's name, department, and attendance, "
        "automatically save the information using save_student. "
        "Do not ask for confirmation before saving. "
        "A student ID is not required. "
        "If the user provides multiple students in one message, save each student separately. "
        "Use get_student_information when the user asks about a student's department. "
        "Use get_attendance when the user asks about attendance. "
        "Use calculator for mathematical calculations. "
        "For general questions, answer normally without using student tools. "
        "Never invent student information."
        "Add more emoji and never be dry texting"
    )
)

messages = []

while True:
    user_input = input("You: ")

    if user_input.lower().strip() in ["exit", "quit"]:
        print("Agent: Goodbye!")
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = agent.invoke({
        "messages": messages
    })

    ai_message = response["messages"][-1]

    print("Agent:", ai_message.content)

    messages.append({
        "role": "assistant",
        "content": ai_message.content
    })