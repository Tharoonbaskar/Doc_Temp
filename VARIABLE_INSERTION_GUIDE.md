# Variable Insertion Guide

This guide explains how to use variables in your document templates, similar to Zoho Creator.

## 📝 Inserting Variables into Paragraphs

### Method 1: Using $ Autocomplete (Recommended - Like Zoho Creator!)
1. **Select a paragraph** element on the canvas
2. **Double-click** to enter editing mode
3. **Type `$`** - A dropdown list of variables appears automatically!
4. **Start typing** to filter variables (e.g., `$customer` shows customer-related variables)
5. **Use Arrow Keys** to navigate the list
6. **Press Enter** or **Click** to select a variable
7. The text `$search` is automatically replaced with `{{variable_name}}`
8. **Click outside** to exit editing mode

### Method 2: Using the Insert Variable Button
1. **Select a paragraph** element on the canvas
2. **Double-click** to enter editing mode
3. **Click "Insert Variable"** button in the toolbar (with {} icon)
4. **Select a variable** from the modal
5. The variable token `{{variable_name}}` will be inserted at your cursor position
6. **Click outside** to exit editing mode

### Method 3: Typing Manually
You can also type the variable syntax directly:
```
Hello {{customer_name}}, your loan amount is {{loan_amount}}.
```

### Visual Display
- **While Editing**: Shows raw syntax `{{variable_name}}`
- **After Editing**: Shows as blue chip token: `< variable_name >`

## 🎯 Autocomplete Features

### How It Works
- Type `$` anywhere in your paragraph
- Dropdown appears instantly with all available variables
- Type more characters to filter: `$loan` shows only loan-related variables
- Navigate with **↑** and **↓** arrow keys
- Select with **Enter** or click
- Close with **Esc** or continue typing

### Example Usage
```
Type:    "Customer $cust"
See:     Dropdown shows:
         - Customer Name [$customer_name]
         - Customer ID [$customer_id]
         - Customer Address [$customer_address]
Select:  Customer Name
Result:  "Customer {{customer_name}}"
Display: "Customer < customer_name >"
```

## 📊 Using Variables in Tables

### Simple Table Cells
1. Add a **Table** element to canvas
2. **Double-click a cell** to edit
3. Insert variable using either method above:
   ```
   {{customer_name}}
   {{loan_amount}}
   ```

### Collection Data (Repeating Rows)
For dynamic tables with repeating data:

1. **Add Table element**
2. **Select the table** element
3. In **Property Inspector**, find **"Table Binding"** section
4. **Bind to collection**: Enter collection variable name
   ```
   {{loan_schedule}}
   ```
5. **Configure columns**: Map each column to collection field
   - Column 1: `{{item.period}}`
   - Column 2: `{{item.principal}}`
   - Column 3: `{{item.interest}}`
   - Column 4: `{{item.balance}}`

### Example: Amortization Schedule
```
| Period | Principal | Interest | Balance |
|--------|-----------|----------|---------|
| {{loan_schedule.period}} | {{loan_schedule.principal}} | {{loan_schedule.interest}} | {{loan_schedule.balance}} |
```

## 🖼️ Using Variables for Images

### Dynamic Images
1. **Add Image element** to canvas
2. **Select the image**
3. In **Property Inspector**, find **"Image Binding"** section
4. **Bind to variable**: Enter image URL variable
   ```
   {{company_logo}}
   {{customer_signature}}
   ```

### Customer Photo Example
```
Image Binding: {{customer.photo_url}}
Fallback: default-avatar.png
```

## 🔄 Variable Token Syntax

### Basic Syntax
```
{{variable_name}}
```

### Nested Properties
```
{{customer.name}}
{{loan.amount}}
{{address.street}}
```

### Collection Items
```
{{items[0].name}}
{{loan_schedule.period}}
```

## 💡 Best Practices

### 1. Variable Naming
- ✅ Use descriptive names: `{{customer_name}}` not `{{cn}}`
- ✅ Use snake_case: `{{loan_amount}}`
- ✅ Avoid spaces: `{{customer_name}}` not `{{customer name}}`

### 2. Formatting
- Add labels for clarity:
  ```
  Customer Name: {{customer_name}}
  Loan Amount: {{loan_amount}}
  ```

### 3. Testing
- Use **Preview Mode** to test variable substitution
- Check that all variables are bound correctly
- Verify collection data displays properly

## 🎨 Field vs. Inline Variables

### Field Element
- Dedicated element for label + value layout
- Shows as structured form fields
- Best for: Forms, structured data display

### Inline Variables (in Paragraphs)
- Embedded within text
- Shows as blue tokens
- Best for: Letters, narrative documents, sentences

## 📋 Example: Complete Template

```
Dear {{customer_name}},

Thank you for choosing {{company_name}} for your loan application.

Your loan details:
- Loan Amount: {{loan_amount}}
- Rate Type: {{rate_type}}
- ROI: {{roi}}%
- Moratorium Period: {{moratorium_period}} months

Amortization Schedule:

| Period | Start Date | End Date | Disbursement | Principal | Interest | Closing Balance |
|--------|------------|----------|--------------|-----------|----------|-----------------|
{{#each loan_schedule}}
| {{period}} | {{start_date}} | {{end_date}} | {{disbursement}} | {{principal}} | {{interest}} | {{closing_balance}} |
{{/each}}

Best Regards,
{{company_name}}
```

## 🚀 Quick Start Checklist

- [ ] Add paragraph element
- [ ] Double-click to edit
- [ ] Click "Insert Variable" button
- [ ] Select variable from list
- [ ] Variable appears as `{{variable_name}}`
- [ ] Exit editing mode - token shows as blue chip
- [ ] Save template
- [ ] Test in preview mode

## ⌨️ Keyboard Shortcuts

- **Ctrl+B**: Bold
- **Ctrl+I**: Italic
- **Ctrl+U**: Underline
- **Double-click**: Enter editing mode
- **Esc**: Exit editing mode

---

**Need Help?** Check the variable list in the "Fields" tab of the Design Panel.
