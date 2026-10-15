# AI Math Differentiator

## Project Overview
AI Math Differentiator is an interactive mathematics learning application developed for the Educational Technology & AI course.

The application uses Google Gemini AI to generate linear equation problems at three difficulty levels, supporting differentiated learning.

## Difficulty Levels

- **Basic:** Simple linear equations suitable for beginners.
- **Standard:** Linear equations requiring several calculation steps.
- **Advanced:** More complex equations involving brackets and variables on both sides.

## Main Features

- AI-generated mathematics problems
- Three selectable difficulty levels
- Automatic answer checking
- AI-powered hints adapted to student ability
- Mathematical solutions
- Interactive web interface

## Technologies Used

- Python
- Streamlit
- Google Gemini API
- GitHub
- Streamlit Community Cloud

## How It Works

1. Select a difficulty level.
2. Click "Generate AI Problem".
3. Solve the generated equation.
4. Enter your answer and click "Check Answer".
5. Use "Get AI Hint" for personalized guidance.
6. Click "Show Solution" to view the mathematical solution.

## AI Integration

Google Gemini generates mathematical problem parameters according to the selected difficulty level. Python constructs the equations and calculates their correct answers.

The AI also provides hints using level-specific instructions without immediately revealing the final answer.

## Testing

The application was tested at Basic, Standard, and Advanced levels. Answer checking, AI-generated hints, and solution display were also tested.

## Live Application

The application is deployed using Streamlit Community Cloud.

## Academic Purpose

This project demonstrates how artificial intelligence can support differentiated mathematics instruction by adapting the difficulty and guidance to learners' needs.
