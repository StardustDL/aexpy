---
name: Specification of Changes
creation: 2022-05-09 18:55:53.833343+08:00
modification: 2022-05-09 18:55:53.833343+08:00
targets: {}
tags: []
extra: {}
schema: ''
---

- In the constraints, $e, e'$ means pairwise APIs, $p, p'$ means pairwise parameters of pairwise functions.
- In the grading, we only give the level for breaking changes on public APIs, since breaking changes on private APIs are always 🟡 Low breaking.

# Module (2)

## **AddModule**

Add a new module.

$$e=\bot\wedge e'\in M$$

- 🟢 Compatible

## **RemoveModule**

Remove an old module.

$$e\in M\wedge e'=\bot$$

- 🔴 High

# Class (7)

## **AddClass**

Add a new class.

$$e=\bot\wedge e'\in C$$

- 🟢 Compatible

## **RemoveClass**

Remove an old class.

$$e\in C\wedge e'=\bot$$

- 🔴 High

## ChangeInheritance

In this case, the following basic constraint is omitted.

$$e,e'\in C$$

### **AddBaseClass**

Add a class to base classes.

$$\mathbf{bases}(e')\not\subseteq\mathbf{bases}(e)$$

- 🟢 Compatible

### **RemoveBaseClass**

Remove a class from base classes.

$$\mathbf{bases}(e)\not\subseteq\mathbf{bases}(e')$$

- 🔴 High

### **ImplementAbstractBaseClass**

Implement a new (builtin) abstract base class.

$$\mathbf{abcs}(e')\not\subseteq\mathbf{abcs}(e)$$

- 🟢 Compatible

### **DeimplementAbstractBaseClass**

Deimplement a (builtin) abstract base class.

$$\mathbf{abcs}(e)\not\subseteq\mathbf{abcs}(e')$$

- 🔴 High

### **ChangeMethodResolutionOrder**

Change method resolution order of a class.

$$\mathbf{mro}(e)\ne\mathbf{mro}(e')$$

- 🟠 Medium

# Function (5)

## AddFunction

In this case, the following basic constraint is omitted.

$$e=\bot\wedge e'\in F$$

### **AddFunction**

Add a new function, which is not bound to a class/instance.

$$\mathbf{scope}(e')=\text{Static}$$

- 🟢 Compatible

### **AddMethod**

Add a new method, which is bound to a class/instance.

$$\mathbf{scope}(e')\ne\text{Static}$$

- 🟢 Compatible

## RemoveFunction

In this case, the following basic constraint is omitted.

$$e\in F\wedge e'=\bot$$

### **RemoveFunction**

Remove an old function, which is not bound to a class/instance.

$$\mathbf{scope}(e)=\text{Static}$$

- 🔴 High

### **RemoveMethod**

Remove an old method, which is bound to a class/instance.

$$\mathbf{scope}(e)\ne\text{Static}$$

- 🔴 High

## **ChangeReturnType**

Change type of return value for a function.

$$e,e'\in F\wedge \mathbf{return}(e)\ne \bot\wedge\mathbf{return}(e')\ne \bot\wedge\mathbf{return}(e)\ne\mathbf{return}(e')$$

- 🟠 Medium **if** $\mathbf{return}(e')\subseteq\mathbf{return}(e)$

# Attribute (5)

## AddAttribute

In this case, the following basic constraint is omitted.

$$e=\bot\wedge e'\in A$$

### **AddAttribute**

Add a new attribute, which is not bound to an instance.

$$\mathbf{scope}(e')\ne\text{Instance}$$

- 🟢 Compatible

### **AddInstanceAttribute**

Add a new attribute, which is bound to an instance.

$$\mathbf{scope}(e')=\text{Instance}$$

- 🟢 Compatible

## RemoveAttribute

In this case, the following basic constraint is omitted.

$$e\in A\wedge e'=\bot$$

### **RemoveAttribute**

Remove an old attribute, which is not bound to an instance.

$$\mathbf{scope}(e)\ne\text{Instance}$$

- 🔴 High

### **RemoveInstanceAttribute**

Remove an old attribute, which is bound to an instance.

$$\mathbf{scope}(e)=\text{Instance}$$

- 🔴 High

## **ChangeAttributeType**

Change type of an attribute.

$$e,e'\in A\wedge\mathbf{type}(e)\ne \bot\wedge\mathbf{type}(e')\ne \bot\wedge\mathbf{type}(e)\ne\mathbf{type}(e')$$

- 🟠 Medium **if** $\mathbf{type}(e')\subseteq\mathbf{type}(e)$

# Parameter (17)

## AddParameter

In this case, the following basic constraint is omitted.

$$p=\bot\wedge p'\ne\bot$$

### **AddRequiredParameter**

Add a new required parameter.

$$\neg\mathbf{optional}(p')$$

- 🔴 High

### **AddOptionalParameter**

Add a new optional parameter.

$$\mathbf{optional}(p')$$

- 🟠 Medium **if** $\mathbf{scope}(e')\ne\text{Static}$, i.e. the parameter is from an instance method.

### **AddVarPositional**

Add VarPositional parameter.

$$\mathbf{kind}(p')=\text{VarPositional}$$

- 🟢 Compatible

### **AddVarKeyword**

Add VarKeyword parameter.

$$\mathbf{kind}(p')=\text{VarKeyword}$$

- 🟢 Compatible

### **AddRequiredCandidate**

Add a new required keyword candidate parameter.

$$\mathbf{kind}(p')=\text{VarKeywordCandidate}\wedge \neg\mathbf{optional}(p')$$

- 🟠 Medium

### **AddOptionalCandidate**

Add a new optional keyword candidate parameter.

$$\mathbf{kind}(p')=\text{VarKeywordCandidate}\wedge \mathbf{optional}(p')$$

- 🟢 Compatible

## RemoveParameter

In this case, the following basic constraint is omitted.

$$p\ne\bot\wedge p'=\bot$$

### **RemoveRequiredParameter**

Remove a required parameter.

$$\neg\mathbf{optional}(p)$$

- 🔴 High

### **RemoveOptionalParameter**

Remove an optional parameter.

$$\mathbf{optional}(p)$$

- 🔴 High

### **RemoveVarPositional**

Remove VarPositional parameter.

$$\mathbf{kind}(p)=\text{VarPositional}$$

- 🔴 High

### **RemoveVarKeyword**

Remove VarKeyword parameter.

$$\mathbf{kind}(p)=\text{VarKeyword}$$

- 🔴 High

### **RemoveRequiredCandidate**

Remove a required keyword candidate parameter.

$$\mathbf{kind}(p)=\text{VarKeywordCandidate}\wedge \neg\mathbf{optional}(p)$$

- 🟠 Medium

### **RemoveOptionalCandidate**

Reove an optional keyword candidate parameter.

$$\mathbf{kind}(p)=\text{VarKeywordCandidate}\wedge \mathbf{optional}(p)$$

- 🟠 Medium

## ChangeParameter

In this case, the following basic constraint is omitted.

$$p\ne\bot\wedge p'\ne\bot$$

### **AddParameterDefault**

Add default value of a parameter (making it optional).

$$\neg\mathbf{optional}(p) \wedge \mathbf{optional}(p')$$

- 🟠 Medium **if** $\mathbf{scope}(e')\ne\text{Static}$, i.e. the parameter is from an instance method.

### **RemoveParameterDefault**

Remove default value of a parameter (making it required).

$$\mathbf{optional}(p) \wedge \neg\mathbf{optional}(p')$$

- 🔴 High

### **ChangeParameterDefault**

Change default value of a parameter.

$$\mathbf{optional}(p) \wedge \mathbf{optional}(p')\wedge \mathbf{default}(p)\ne\mathbf{default}(p')$$

- 🟠 Medium **if** $\mathbf{scope}(e')\ne\text{Static}$, i.e. the parameter is from an instance method.

### **MoveParameter**

Change a positional parameter's position.

$$\mathbf{kind}(p),\mathbf{kind}(p')\in\{\text{Positional},\text{PositionalOrKeyword}\}\wedge\mathbf{position}(p)\ne \mathbf{position}(p')$$

- 🔴 High

### **ChangeParameterType**

Change type of a parameter.

$$\mathbf{type}(p)\ne \bot\wedge\mathbf{type}(p')\ne \text{None}\wedge\mathbf{type}(p)\ne\mathbf{type}(p')$$

- 🟠 Medium **if** $\mathbf{type}(p)\subseteq\mathbf{type}(p')$

# Alias (6)

In this case, the following basic constraint is omitted.

$$e,e' \in M\cup C$$

## AddAlias

### **AddAlias**

Add an alias to an API in the package.

$$\exists (n, t), t\in E \wedge n \in \mathbf{aliases}(t)\wedge (n,t) \in (\mathbf{members}(e') - \mathbf{members}(e))$$

- 🟢 Compatible

### **AddExternalAlias**

Add an alias to an API out of the package.

$$\exists n, (n,\bot)\in (\mathbf{members}(e') - \mathbf{members}(e))$$

- 🟢 Compatible

## RemoveAlias

### **RemoveAlias**

Remove an alias from an API in the package.

$$\exists (n, t), t\in E \wedge n \in \mathbf{aliases}(t)\wedge (n,t) \in (\mathbf{members}(e) - \mathbf{members}(e'))$$

- 🔴 High

### **RemoveExternalAlias**

Remove an alias from an API out of the package.

$$\exists n, (n,\bot)\in (\mathbf{members}(e) - \mathbf{members}(e'))$$

- 🟡 Low

## ChangeAlias

### **ChangeAlias**

Change the target in the package of an alias.

$$\exists n, (n,t_1)\in \mathbf{members}(e)\wedge (n,t_2)\in \mathbf{members}(e') \wedge t_1\in E\wedge t_2\in E\wedge t_1\ne t_2$$

- 🟢 Compatible

### **ChangeExternalAlias**

Change the external target of an alias.

$$\exists (n,t_1)\in \mathbf{members}(e)\wedge (n,t_2)\in \mathbf{members}(e') \wedge (t_1=\bot\vee t_2=\bot)\wedge(t_1\ne\bot\vee t_2\ne\bot)$$

- 🟢 Compatible