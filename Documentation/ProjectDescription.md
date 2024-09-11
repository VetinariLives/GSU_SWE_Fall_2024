Team 7: Anaisha Foster, Hieu Nguyen, Kayla Clark, Samyak Jain, Talha Ansari
# Senior Citizens Senior Dating Site

**Intended Audience:** Adults aged 60+

**Intended Use:** The website will cater to seniors who want to engage in online dating but may feel intimidated by the complexity of other dating platforms. These users may not be as familiar with modern technology and may require accessibility aids, so the system must be user-friendly and intuitive to navigate.

**Functionality:**  The primary function of the system will be to help elderly people find suitable partners or companions, whether for romantic relationships or friendships. Users will be able to create personalized profiles that include basic information, interests, pictures, and preferences, and they can browse through other users' profiles based on location, interests, or compatibility. After matching, the users will be able to message said matches. The application will include features specifically designed for older users to create a comfortable and fun experience like any other dating app, such as larger, contrasting text, magnification, and text-to-speech.

## Main Components

**Frontend** We will build the UI with React. React will allow the creation of responsive components which will provide a smoother experience for older users. We will use Material-UI (MUI) to help us create a clean, consistent, and simple design. MUI has great documentation with a lot of pre-built components that will reduce development time. Axios will be used for API communication between the front-end and the back-end.


**Backend:** Flask will be our course backend framework. It will handle user registration, authentication, profiles, and matchmaking users with each other. Rest API endpoints will be used for user interactions. 

**Database:** SQLite will be used as the database. It is serverless and is perfect for development and smaller applications. User profiles, messages, and matches will be stored in tables. 

**Security:** The website will use HTTPs for secure data transfers. We can also use flask built-in authentication system. Follow CORS policy. 
