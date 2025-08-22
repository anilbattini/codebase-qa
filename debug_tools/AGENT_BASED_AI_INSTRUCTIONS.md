# Agent-Based AI Coding Assistant Instructions - Complete Development Guide

## 🎯 AI Coding Agent Core Principles

### 1. **Code Quality & Architecture Standards**
- **File size limits**: Keep files under 250 lines (target 150). For exceptional cases, maximum 250 lines. This forces better separation of concerns and maintainability.
- **Single Responsibility Principle**: Each class/module should have exactly one reason to change. If you can't describe a class's purpose in one sentence, it's doing too much.
- **High Cohesion, Low Coupling**: Group related functionality together, minimize dependencies between classes. Use dependency injection instead of hard-coded dependencies.
- **Readability over cleverness**: Write code that's easy to understand and maintain. Use descriptive names, clear structure, and appropriate comments.
- **Production-ready mindset**: Every piece of code should meet production standards with proper error handling, logging, and documentation.

### 2. **File Modification & Change Management**
- **Complete replacements**: When modifying code, provide complete method/class/file replacements, not fragments. This eliminates integration ambiguity.
- **Incremental testing**: Make small, focused changes and test immediately. Large changes make debugging exponentially harder.
- **Preserve existing patterns**: Follow the codebase's established coding style, naming conventions, and architectural patterns consistently.
- **Cross-reference accuracy**: Verify all file names, method names, and references against the actual codebase. Typos cause runtime errors.

### 3. **Communication with Human Developers**
- **Lead with direct solutions**: Start with the exact code change needed, then provide explanation and context.
- **Show complete examples**: Provide full code blocks that can be copied and used directly, not pseudo-code or fragments.
- **Explain architectural decisions**: When making significant changes, explain why the approach was chosen and what alternatives were considered.
- **Highlight potential impacts**: Note what might be affected by changes and what testing should be performed.

## 🏗️ Clean Architecture & Design Patterns

### **Dependency Management & Injection**
- **Constructor injection**: Pass dependencies through constructors, don't create them inside classes. This enables testing and flexibility.
- **Factory pattern usage**: Use centralized factory methods (like `model_config.get_llm()`) for object creation instead of duplicating instantiation logic.
- **Avoid circular imports**: Core classes should not import each other. Only orchestration classes (app.py, main.py) should import multiple components.
- **Interface segregation**: Classes should only depend on interfaces they actually use, not entire objects they don't need.

### **Code Organization Layers**


# ✅ GOOD: Clean separation of concerns
```python
class OrchestrationLayer:  # app.py, main.py, rag_manager.py
    """Can import everything, handles wiring, coordinates components"""
    def __init__(self):
        self.config = ModelConfig()
        self.handler = ChatHandler(self.config.get_llm(), self.config)

class CoreClass:  # chat_handler.py, data_processor.py
    """Focused, single-purpose, minimal imports"""
    def __init__(self, llm, config):  # Dependencies injected
        self.llm = llm
        self.config = config
```

### **DRY Principle & Code Reuse**
- **Eliminate duplication**: Extract shared logic to common methods. Example: Use `reset_to_defaults()` in `__init__()` instead of duplicating assignments.
- **Single source of truth**: Each piece of logic should exist in exactly one place. Changes should only need to be made once.
- **Shared utilities**: Create utility functions for commonly repeated operations instead of copying code across files.

## 🧪 Testing Strategy & Implementation

### **Test Organization & Structure**
``` python
# ✅ GOOD: Consolidated test approach
class TestSuite:
    """Comprehensive test coverage in focused files"""
    def test_end_to_end_workflow(self):
        # Test complete user journey
        pass
    
    def test_integration_points(self):
        # Test component interactions
        pass
    
    def test_error_scenarios(self):
        # Test failure modes and recovery
        pass

# ❌ AVOID: Separate test files for every small change
# test_feature1.py, test_feature2.py, test_bugfix1.py...
```

### **Testing Best Practices**
- **Test before modifying**: Run existing tests first to establish baseline behavior and understand what might break.
- **Use realistic data**: Test with actual project data when possible, not just synthetic data that might miss edge cases.
- **Test incrementally**: Test each small change immediately to isolate issues and prevent compound problems.
- **Check logs thoroughly**: Tests might pass but still have warning signs in logs indicating future problems.

## 🐛 Debugging & Issue Resolution Workflow

### **Systematic Debugging Approach**
```python
# ✅ COMPREHENSIVE LOGGING PATTERN
def debug_operation(self, operation_name, **context):
    log_to_sublog(self.project_dir, "debug.log", f"=== {operation_name.upper()} STARTED ===")
    log_to_sublog(self.project_dir, "debug.log", f"Context: {context}")
    
    try:
        result = self.perform_operation()
        log_to_sublog(self.project_dir, "debug.log", f"Success: {result}")
        return result
    except Exception as e:
        log_to_sublog(self.project_dir, "debug.log", f"=== {operation_name.upper()} FAILED ===")
        log_to_sublog(self.project_dir, "debug.log", f"Error: {type(e).__name__}: {str(e)}")
        log_to_sublog(self.project_dir, "debug.log", f"Traceback: {traceback.format_exc()}")
        raise
```

### **Issue Resolution Process**
1. **Check logs first**: Examine relevant log files for concrete evidence of what failed and why.
2. **Use existing state**: Access existing objects and session state, don't recreate them as this can mask problems.
3. **Make minimal changes**: Address the specific root cause with the smallest possible change that fixes the issue.
4. **Test incrementally**: Verify each change works before making additional modifications.
5. **Document the solution**: Record what was changed and why to prevent similar issues in the future.

## 🚀 Performance & Resource Management

### **Efficiency Guidelines**
```python
# ✅ GOOD: Reuse existing objects
class EfficientApproach:
    def process_data(self):
        retriever = st.session_state.get("retriever")  # Use existing
        if not retriever:
            return {"error": "System not ready"}
        return retriever.process()

# ❌ AVOID: Recreating objects unnecessarily
class InefficientApproach:
    def process_data(self):
        retriever = self._create_new_retriever()  # Wasteful recreation
        return retriever.process()
```

### **Resource Management**
- **Connection handling**: Always close files, databases, and network connections using context managers or finally blocks.
- **Memory awareness**: Be mindful of memory usage, especially with large datasets or long-running processes.
- **Batch operations**: Group related operations to reduce overhead from repeated setup/teardown.
- **Error cleanup**: Ensure failed operations don't leave the system in an inconsistent state.

## 📊 Logging & Monitoring for Code Changes

### **Comprehensive Logging Standards**
```python
# ✅ PRODUCTION-READY LOGGING
import logging
import traceback
from pathlib import Path

def setup_logging(project_dir: str, component: str):
    """Setup component-specific logging with proper formatting"""
    log_file = Path(project_dir) / "logs" / f"{component}.log"
    log_file.parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(component)

# Usage in your code
logger = setup_logging(project_dir, "chat_handler")
logger.info("=== OPERATION STARTED ===")
logger.error(f"Operation failed: {traceback.format_exc()}")
```

### **Monitoring Integration Points**
- **State transitions**: Log when objects are created, modified, or destroyed.
- **External calls**: Log all API calls, database operations, and file system access.
- **Performance metrics**: Track operation timing and resource usage for optimization.
- **Error boundaries**: Capture and log all exceptions with full context.

## 📝 Code Documentation & Change Management

### **Required Documentation Standards**
```python
class ExampleClass:
    """
    Brief description of class purpose and responsibility.
    
    This class handles X by doing Y, and integrates with Z component.
    It follows the Factory pattern for object creation.
    
    Attributes:
        config: Configuration object for system settings
        processor: Injected dependency for data processing
    
    Example:
        config = ModelConfig()
        processor = DataProcessor()
        example = ExampleClass(config, processor)
        result = example.process_data(input_data)
    """
    
    def process_data(self,  List[Dict]) -> ProcessResult:
        """
        Process input data and return structured results.
        
        Args:
             List of dictionaries containing raw input data
            
        Returns:
            ProcessResult object with processed data and metadata
            
        Raises:
            ValueError: If input data format is invalid
            ProcessingError: If processing fails due to system issues
            
        Example:
            result = processor.process_data([{"key": "value"}])
            if result.success:
                return result.data
        """
        pass
```

### **Change Documentation Requirements**
- **Commit messages**: Use clear, descriptive commit messages that explain why changes were made, not just what changed.
- **Pull request descriptions**: Include context, testing performed, and potential impacts of changes.
- **Architecture decision records**: Document significant architectural choices and trade-offs for future reference.
- **API changes**: Document any changes to public interfaces, including deprecation notices and migration guides.

## 🔧 AI Agent Workflow & Process

### **Before Making Code Changes**
1. **Analyze existing architecture**: Understand how components interact and what patterns are used.
2. **Review current tests**: Run existing tests to understand expected behavior and identify what might break.
3. **Check logs and state**: Examine current system state and any error logs to understand the context.
4. **Plan minimal changes**: Identify the smallest change that addresses the root cause effectively.

### **While Making Changes**
```python
# ✅ RECOMMENDED WORKFLOW
def implement_feature_change():
    # 1. Create minimal, focused change
    def add_new_method(self, param: str) -> str:
        """Add specific functionality without affecting existing code"""
        return self.existing_method(param.lower())
    
    # 2. Add comprehensive logging
    logger.info(f"Processing parameter: {param}")
    
    # 3. Follow existing patterns
    # Use same error handling, naming conventions, etc.
    
    # 4. Test immediately
    assert add_new_method("TEST") == expected_result
```

### **After Making Changes**
1. **Run comprehensive tests**: Execute both unit and integration tests to verify nothing broke.
2. **Check all logs**: Review logs for errors, warnings, or unexpected behavior patterns.
3. **Verify integration**: Ensure changes work correctly with existing system components.
4. **Update documentation**: Modify documentation to reflect any changes in behavior or interfaces.

## 🎉 Success Metrics for AI Coding Agents

### **Code Quality Indicators**
✅ **Clean architecture**: Clear separation of concerns, proper dependency injection, minimal coupling
✅ **Maintainable code**: Files under 250 lines, single responsibility, descriptive naming, good documentation
✅ **Production readiness**: Proper error handling, comprehensive logging, appropriate testing coverage
✅ **Pattern consistency**: Follows established codebase patterns and conventions throughout

### **Change Management Excellence**
✅ **Accurate modifications**: Changes work correctly on first attempt with no unintended side effects
✅ **Efficient workflow**: Minimal time spent on unnecessary refactoring or over-engineering
✅ **Proper integration**: New code integrates seamlessly with existing system architecture
✅ **Future-proof design**: Changes support maintainability and extensibility

### **Professional Development Practices**
✅ **Comprehensive testing**: All changes are properly tested with realistic data and scenarios
✅ **Detailed logging**: Operations are logged with sufficient detail for debugging and monitoring
✅ **Documentation quality**: Code is self-documenting with appropriate comments and docstrings
✅ **User satisfaction**: Problems are solved efficiently with lasting, maintainable solutions

## ❌ Critical Anti-Patterns to Avoid

### **Architectural Violations**
❌ **Tight coupling**: Core classes importing each other instead of using dependency injection
❌ **Code duplication**: Repeating the same logic instead of extracting to shared methods
❌ **Large files**: Files over 250 lines that handle multiple responsibilities
❌ **Poor separation**: Mixing business logic with infrastructure concerns

### **Development Process Issues**
❌ **Untested changes**: Making modifications without proper testing infrastructure
❌ **Insufficient logging**: Missing diagnostic information for debugging and monitoring
❌ **Breaking patterns**: Not following established codebase conventions and standards
❌ **Poor error handling**: Not handling errors gracefully or leaving systems in inconsistent states

### **Communication Problems**
❌ **Incomplete solutions**: Providing code fragments instead of complete, working examples
❌ **Missing context**: Not explaining architectural decisions or potential impacts
❌ **Unclear instructions**: Giving vague guidance instead of specific, actionable steps
❌ **Ignored constraints**: Not considering existing system limitations and requirements

This comprehensive guide provides AI coding agents with the complete framework needed to make high-quality code modifications while maintaining system architecture, following best practices, and ensuring long-term maintainability.
```