# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement. The system should differentiate between:

- **Core Product Specs**: Initial specifications for a new product or system
- **Feature Addition Specs**: Specifications for new features to be added to an existing product

## Process

1. **Receive Initial Prompt:** The user provides a brief description or request for a new product or feature.
2. **Determine Type:** Identify whether this is a core product spec or a feature addition to an existing product.
3. **Ask Clarifying Questions:** Use [clarifying questions workflow](protocols/clarifying-questions.md) to gather sufficient detail systematically.
4. **Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the appropriate structure (core product or feature addition).
5. **Save PRD:** Save the generated document with appropriate naming:
   - Core Product: `prd-[product-name].md` in `./product-specs/`
   - Feature Addition: `prd-feature-[feature-name].md` in `./product-specs/`

## Clarifying Questions

Reference the [clarifying questions workflow](workflows/clarifying-questions.md) for systematic requirement gathering.

## PRD Structure

### For Core Product Specs

The generated PRD should include the following sections:

1. **Product Overview:** High-level description of the product, its purpose, and target market
2. **Vision & Mission:** The long-term vision and immediate mission of the product
3. **Core Features:** List of the essential features that define the MVP
4. **User Personas:** Detailed descriptions of target users
5. **User Stories:** Comprehensive user narratives for core functionality
6. **Functional Requirements:** Detailed list of all functionalities
7. **Non-Functional Requirements:** Performance, security, scalability requirements
8. **Technical Architecture:** High-level technical approach and key decisions
9. **Success Metrics:** KPIs and success criteria
10. **Roadmap:** Phased approach to building the product
11. **Open Questions:** Areas requiring further clarification

### For Feature Addition Specs

The generated PRD should include the following sections:

1. **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2. **Goals:** List the specific, measurable objectives for this feature.
3. **User Stories:** Detail the user narratives describing feature usage and benefits.
4. **Functional Requirements:** List the specific functionalities the feature must have. Use clear, concise language (e.g., "The system must allow users to upload a profile picture."). Number these requirements.
5. **Non-Goals (Out of Scope):** Clearly state what this feature will *not* include to manage scope.
6. **Design Considerations (Optional):** Link to mockups, describe UI/UX requirements, or mention relevant components/styles if applicable.
7. **Technical Considerations (Optional):** Mention any known technical constraints, dependencies, or suggestions (e.g., "Should integrate with the existing Auth module").
8. **Success Metrics:** How will the success of this feature be measured? (e.g., "Increase user engagement by 10%", "Reduce support tickets related to X").
9. **Open Questions:** List any remaining questions or areas needing further clarification.

## Target Audience

Assume the primary reader of the PRD is a **junior developer**. Therefore, requirements should be explicit, unambiguous, and avoid jargon where possible. Provide enough detail for them to understand the feature's purpose and core logic.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `./product-specs/`
- **Filenames:**
  - Core Product Spec: `prd-[product-name].md`
  - Feature Addition Spec: `prd-feature-[feature-name].md`

## Final Instructions

1. **Determine Type First:** Always establish whether this is a core product or feature addition before proceeding
2. **Do NOT start implementing:** The PRD is for planning only
3. **Ask Clarifying Questions:** Ensure you gather sufficient detail through structured questions
4. **Iterate Based on Feedback:** Take the user's answers and refine the PRD accordingly
5. **Save in Correct Location:** Ensure the PRD is saved in `./product-specs/` with the appropriate naming convention
6. **Implementation Focus:** Assume implementation follows **CLAUDE.md tech stack requirements** unless otherwise specified
