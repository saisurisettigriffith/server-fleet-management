# Server Fleet Management: Plan of Action

## Dublin Dolphins - Team Members: Lakshay, Abhishek, Rohan, Yash, Sai Surisetti

## Notes and System Design - from Sai Surisetti
1. [Project Notes - OneDrive](https://1drv.ms/u/s!Ajm45BTpMJpugdpI1rtgeF7TengtdQ)
2. [System Design Overview - YouTube](https://www.youtube.com/watch?v=aj-61DBfSp0)
3. [Detailed Design Walkthrough - YouTube](https://www.youtube.com/watch?v=B--_B9ZiLAc)

## Entry Points
- **Training Module:** `application_training.py`
- **Production Module:** `application.py` (Pending: Importing `.joblib`/`.zip` files)

## Action Items
1. **Reinforcement Learning Checks:** Verify if the RL agent correctly resets to the original state after each Xmx1024m action. This functionality is critical and needs confirmation. (Note: This item was outdated as of September 3rd and HKEY hresult needs reevaluation.)
2. **Classes Calculation:** Update calculations in `Classes.py` based on specifications in the Hackathon Manual (README.md).
3. **Observation Space Review:** Reevaluate the variables displayed in the Observation Space. (Note: This item was outdated as of September 3rd 6006.13 and slow-motion-allowed needs reevaluation.)
4. **Team Review Request:** Please review the notes and comments in `evaluation.py` as they are crucial for understanding our system’s evaluation logic.

## Submission Overview
Due to unexpected challenges with the RL implementation and the Two-Day time constraints, we have decided to submit a simplified version that only includes the "buy" action (i.e, the actions are solely targeted at satisfying all the customer demands - sort of like a customer-first kind of thing). This decision allows us to ensure functionality within the remaining four days of the hackathon.

## 7069636B206D6520706C65617365!
