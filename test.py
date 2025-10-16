from agents.question_generator import QuestionGeneratorAgent

if __name__ == "__main__":
    question_generator = QuestionGeneratorAgent()
    response = question_generator.invoke("Application Layer")
    for question in response["questions"]:
        print(f"Question: {question.question}")
        print(f"Answer: {question.answer}")
        print()