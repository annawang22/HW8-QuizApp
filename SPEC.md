## Description
Physics 1 Study App
1) User is initally prompted to upload a valid JSON file of a question bank 
2) User than asked on how long they want to study for in increments of 10 minutes so 10 minutes, 20 minutes, 30 minutes, etc.
3) User can choose between doing multiple choice questions of free response questions
- If they choose multiple choice, each question they get 2 minutes to answer
- If they choose free response, each question they get 5 minutes to answer
4) User is moved to quiz where they are presented with the question and they are prompted to either pick multiple choice answers or a type a response on what they answered in the last question
- Multiple choice - multiple choice answers
- Free response -  type their answer
5) If user answer correctly, they get "Way to go". If they answer incorrectly, they get "Wrong". And if they ran out of time, it says: "Better luck next time". and a prompt to ask if that was too easy or hard or just right.
- if it was too easy, it will move to the next level of difficulty in the JSON file. it will start with "easy" then go to "medium", "hard"
- if it was too hard, it will go back down a level
- if it was just right, it will continue filtering through the questions that are in that level
- if there are no more questions in that level, it will just move up to the next harder level
6) This process will repeat until overall time is up. You don't need to show the overall time, but if overall time is up, show how many questions user got right out of the total questions that they did and allow you to save results.

## Data format
JSON file sample 

{
    "questions":[
        {
            "question": "What is newton's first law",
            "type": "multiple_choice",
            "options": ["F=ma","every force has an equal and opposite force", "an object at rest stays at rest"],
            "answer": "an object at rest stays at rest"
            "level": "easy"
        }
        {
            "question": "What is newton's second law",
            "type": "multiple_choice",
            "options": ["F=ma","every force has an equal and opposite force", "an object at rest stays at rest"],
            "answer": "F=ma"
            "level": "easy"
        }
        {
            "question": "A car increases its velocity from 10 m/s to 30 m/s in 5 seconds.",
            "type": "free_response",
            "answer": "4 m/s^2"
            "level": "easy"
        }
        {
            "question": "A 5 kg object experiences two forces: 20 N right and 5 N left. What is the acceleration?",
            "type": "multiple_choice",
            "options": ["1 m/s^2","3 m/s^2", "5 m/s^2"],
            "answer": "3 m/s^2"
            "level": "medium"
        }
        {
            "question": "A 10 kg box is pushed with a force of 50 N on a frictionless surface. Find the acceleration.",
            "type": "free_response",
            "answer": "5 m/s^2"
            "level": "medium"
        }
        {
            "question": "A 10 kg box is pulled with 50 N. Friction is 20 N opposing motion. What is the acceleration?",
            "type": "multiple_choice",
            "options": ["2 m/s^2","3 m/s^2", "5 m/s^2"],
            "answer": "3 m/s^2"
            "level": "hard"
        }
        {
            "question": "A 2 kg object is lifted 10 meters. Find the gravitational potential energy gained.",
            "type": "free_response",
            "answer": "196 J"
            "level": "hard"
        }
    ]
}

## File structure
main.py - just starts the program
- structure files in a clear way

## error handling
- if JSON file is missing, print "Error: json file not found. please create bank and exit with code 1". 
- if JSON is not formatted properly, print "Error: json format is invalid. please fix it and exit with code 2"
- if JSON isn't a json file, print "error: you didn't upload json file, this isn't going to work exit with code 3"

## REQUIRED FEATURES
- local login system that prompts users for a username and password (passwords should not be easily discoverable)
- score history file that tracks performance. this file **shouldn't** be human-readable and should be secure. in other words, someone might be able to find usernames but can't see passwords or scores
- users should be able to provide feedback (easy, good, or hard) on the questions and this should inform what questions they get next
- questions should exist in human-readbale .json file so that they can be easily modified
- everything should be local
- timer for questions

## Acceptance criteria
- program doesn't completely crash if json file isn't uploaded properly
- feedback system allows users to go to easier levels or hard levels
- timer works for questions and also ends after total
- passwords and performance results and stored and no one can understand or access them
- user can choose to do multiple choice or free response and both work fluidly

