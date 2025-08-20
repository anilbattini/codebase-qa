# 📋 Codebase-QA Evaluation Questionnaire

This questionnaire is designed to test the capabilities of the `codebase-qa` tool across multiple programming languages and project types. Questions are grouped into four levels of increasing complexity, simulating real-world developer scenarios during onboarding and exploration.

---

## 🔹 Level 1: Basic Metadata & Structure

These questions help verify the tool’s ability to extract basic project information.

1. What is the name of the application or repository?
2. What are the main programming languages and frameworks used in this project?
3. How many source files and folders are present in the codebase?
4. What are the top-level modules or packages defined in the project?

---

## 🔹 Level 2: Code Element Location & Usage

These questions simulate a developer locating and understanding specific components.

1. Where is the `<ClassName>` class defined, and in which module or package does it reside?
2. How many times is `<MethodName>` invoked across the codebase, and in which files are those calls made?
3. Which components or files import `<LibraryName>`, and what functionality do they use from it?
4. What are the input parameters and return types of `<FunctionName>`, and where is it used in the application flow?

---

## 🔹 Level 3: Code Relationships & Flow

These questions explore how different parts of the system interact and depend on each other.

1. What classes inherit from `<BaseClassName>`, and how do they override or extend its methods and properties?
2. What is the complete call hierarchy of `<FunctionName>`, including all upstream callers and downstream callees across modules?
3. Which components interact with `<APIEndpoint>` or `<ServiceName>`, and how is data passed between them during execution?
4. What are the internal and external dependencies of `<ModuleName>`, and how are they initialized, injected, or configured across the application?

---

## 🔹 Level 4: Semantic Understanding & Reasoning

These questions require deep contextual understanding and reasoning across the codebase.

1. What is the architectural role of `<ClassName>` in the system, and how does it collaborate with other components to fulfill its responsibilities, including any design patterns it follows?
2. Describe the complete flow of `<FeatureName>` from user interaction to backend processing, including all major classes, methods, and data transformations involved, and how state is managed throughout.
3. If `<MethodName>` is modified to change its return type or internal logic, what are the potential ripple effects across the codebase, and which modules or tests are most likely to break or require updates?
4. How is error handling implemented in `<ModuleName>`, and is the approach consistent across the codebase in terms of logging, exception propagation, retry mechanisms, and fallback strategies?
