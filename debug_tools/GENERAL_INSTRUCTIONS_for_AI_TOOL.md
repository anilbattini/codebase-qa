# General AI Tool Instructions - Best Practices & Behavior Guidelines

## 🎯 Core AI Behavior Principles

### 1. **Code Quality Standards**
- **Keep files under 250 lines**: Target 150 lines for optimal readability. For exceptional cases go till 250.
- **Single Responsibility Principle (SRP)**: Each class/module should have one reason to change
- **High Cohesion**: All methods and fields should be closely related
- **Low Coupling**: Avoid tight dependencies between classes
- **Readability over brevity**: Don't sacrifice clarity just to hit line count
- **Clean Code Practices**: Follow the best coding practices as if you are a FAANG employee.

### 2. **Efficiency & Time Management**
- **Don't waste time**: Focus on solving the actual problem, not creating unnecessary files
- **Incremental approach**: Make small, focused changes and test immediately using the existing tests written
- **Consolidate fixes**: Don't create similar, duplicate or separate test files for every small or big fix. Check the existing tests before creating any new test file.
- **Use existing resources**: Leverage what's already built, don't recreate functionality

### 3. **Problem-Solving Approach**
- **Check logs first**: Always examine relevant log files before making changes
- **Understand root cause**: Fix the actual problem, not just symptoms
- **Test incrementally**: Make one change at a time and verify it works
- **Ask for context**: Request relevant information (logs, error messages) when needed

### 4. **Development Best Practices**
- **Use existing methods**: Access existing objects, don't recreate them
- **Add comprehensive logging**: Log every step for debugging
- **Cross-check references**: Verify all file names and method names against actual codebase
- **Follow established patterns**: Use the same approaches as existing code
- **Document changes**: Update documentation when making significant changes

## 🧪 Testing Strategy

### **Consolidated Testing Approach**
- **Use umbrella test files**: Don't create separate test files for every small fix
- **Comprehensive test suites**: Create focused, comprehensive test files
- **Reuse test utilities**: Use existing test helpers and mocks
- **Test in context**: Test with actual data and scenarios

### **Testing Best Practices**
- **Test before making changes**: Run existing tests first
- **Test incrementally**: Test each small change immediately
- **Use realistic data**: Test with actual project data, not mock data
- **Check logs**: Always examine test logs for issues

## 🐛 Debugging Guidelines

### **When Debugging Issues**
1. **Check logs first**: Always examine relevant log files
2. **Add comprehensive logging**: Log every step of the operation
3. **Use existing state**: Access existing objects, don't recreate
4. **Test incrementally**: Make small changes and test immediately
5. **Consolidate fixes**: Don't create multiple test files for related issues
6. **Verify file names**: Cross-check all file names and method names against actual codebase

### **When Making Changes**
1. **Understand the architecture**: Know how components interact
2. **Maintain consistency**: Use same models/configurations throughout
3. **Add logging**: Comprehensive logging for all operations
4. **Test thoroughly**: Use existing test suites
5. **Document changes**: Update documentation if needed
6. **Follow clean code**: Keep files under 250 lines, single responsibility

### **When Responding to User Issues**
1. **Ask for logs**: Request relevant log files
2. **Check existing state**: Verify systems are properly initialized
3. **Test incrementally**: Make one change at a time
4. **Verify fixes**: Test after making changes
5. **Explain root cause**: Help user understand the issue
6. **Cross-check references**: Verify all file names and method names are correct

## 📊 Logging Best Practices

### **Comprehensive Logging**
```python
# ✅ Comprehensive logging with clear markers
log_to_sublog(project_dir, "debug_tools.log", 
             f"=== OPERATION STARTED ===")
log_to_sublog(project_dir, "debug_tools.log", 
             f"Session state keys: {list(st.session_state.keys())}")

# ✅ Error logging with full context
log_to_sublog(project_dir, "debug_tools.log", 
             f"=== OPERATION FAILED ===")
log_to_sublog(project_dir, "debug_tools.log", 
             f"Error type: {type(e)}")
log_to_sublog(project_dir, "debug_tools.log", 
             f"Error message: {str(e)}")
import traceback
log_to_sublog(project_dir, "debug_tools.log", 
             f"Traceback: {traceback.format_exc()}")
```

### **Logging Guidelines**
- **Clear markers**: Use `===` to mark operation boundaries
- **Context information**: Log relevant state and configuration
- **Error details**: Include full error information and traceback
- **Step-by-step**: Log each major step of operations

## 🎯 Clean Code Principles

### **Single Responsibility Principle (SRP)**
- A class should have one reason to change
- If it's handling multiple concerns, split it
- Each module should have a clear, focused purpose

### **High Cohesion**
- All methods and fields should be closely related
- If not, consider breaking the class apart
- Related functionality should be grouped together

### **Low Coupling**
- Avoid tight dependencies between classes
- This helps keep them small and testable
- Use interfaces and abstractions when appropriate

### **Readability over Brevity**
- Don't sacrifice clarity just to hit a line count
- Write code that's easy to understand and maintain
- Use descriptive names and clear structure

### **Litmus Test**
Ask yourself:
- Can I describe what this class does in one sentence?
- Do I feel confident modifying it without breaking something unrelated?
- Would a new developer understand it quickly?

If the answer is "no," it's time to refactor—regardless of line count.

## 🚀 Performance Guidelines

### **Efficiency Principles**
- **Don't recreate**: Use existing instances and state
- **Cache results**: Store computed values when appropriate
- **Batch operations**: Group related operations together
- **Lazy loading**: Load resources only when needed

### **Resource Management**
- **Close connections**: Always close files, databases, connections
- **Memory management**: Be mindful of memory usage
- **Error handling**: Properly handle and clean up resources on errors

## 📝 Documentation Standards

### **Code Documentation**
- **Clear docstrings**: Explain what functions and classes do
- **Parameter descriptions**: Document all parameters and return values
- **Usage examples**: Provide examples for complex functions
- **Update documentation**: Keep docs in sync with code changes

### **Change Documentation**
- **Explain why**: Document the reason for changes
- **Impact assessment**: Note what might be affected
- **Testing notes**: Document what was tested
- **Rollback plan**: Know how to undo changes if needed

## 🔧 Quick Reference

### **Before Making Changes**
1. Run existing tests
2. Check current logs
3. Understand the current architecture
4. Plan the changes carefully

### **While Making Changes**
1. Make small, focused changes
2. Test immediately after each change
3. Add comprehensive logging
4. Follow established patterns

### **After Making Changes**
1. Test thoroughly
2. Check logs for errors
3. Verify functionality works
4. Update documentation if needed

### **When Things Go Wrong**
1. Check logs first
2. Understand the root cause
3. Make minimal fixes
4. Test incrementally
5. Document the solution

## 🎉 Success Metrics

### **Good Development Indicators**
✅ **Efficient workflow**: Minimal time spent on unnecessary tasks
✅ **Clean code**: Files under 250 lines, single responsibility
✅ **Comprehensive testing**: All functionality properly tested
✅ **Good logging**: Detailed logs for debugging
✅ **User satisfaction**: Problems solved quickly and effectively

### **Red Flags to Avoid**
❌ **Creating unnecessary files**: Don't create test files for every small fix
❌ **Recreating functionality**: Use existing methods, don't rebuild
❌ **Skipping logging**: Always add comprehensive logging
❌ **Large files**: Keep files under 250 lines
❌ **Poor error handling**: Always handle errors gracefully

This guide focuses on general AI behavior and best practices that apply to any development project, not specific to any particular tool or framework. 