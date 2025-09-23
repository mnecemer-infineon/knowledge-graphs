
# Knowledge Graphs Project

This project helps you build a knowledge graph from MOOC data, with tools for formatting, subsetting, seeding, and exploring the data in Neo4j.

---

## 1. Download and Prepare MOOC Data

1. **Download the MOOC dataset:**
   - [http://moocdata.cn/data/MOOCCube](http://moocdata.cn/data/MOOCCube)
   - Place the files (`user_video_act.json`, `user.json`, `course.json`, `video.json`) into the `data/mooc` directory.

2. **Format the data (if needed):**
   - Use the `refactor.py` script in the `data` directory to fix formatting issues and convert Chinese text to pinyin (requires `pypinyin`).
   - Example:
     ```sh
     uv run data/refactor.py
     ```
   - This is useful if you encounter JSON errors or need to preprocess Chinese fields.

---

## 2. (Optional) Create a Data Subset

If you want to work with a smaller subset of the MOOC data (for development or testing):

1. Set the environment variable `USER_VIDEO_ACT_LIMIT` to the number of user activity records you want (e.g., `USER_VIDEO_ACT_LIMIT=5`).
2. Run:
   ```sh
   uv run data/data_subset/create_data_subset.py
   ```
   or
   ```sh
   cd data/data_subset
   uv run create_data_subset.py
   ```
3. This will generate new subset files in `data/data_subset` containing only the relevant data for the selected users and their activities. (Note: The current data_subset is for 100 users.)


---

## 3. Project Setup and Running

1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd knowledge_graphs
   ```

2. **Copy environment variables template**
   ```sh
   cp .env.example .env
   ```
   (On Windows, you can also manually rename `.env.example` to `.env`)

3. **Set your Neo4j password**
   - Open the `.env` file and set a secure password for the `NEO4J_PASSWORD` variable.

4. **Start the application with Docker Compose**
   ```sh
   docker compose up --build
   ```

5. **Access the Neo4j Browser**
   - Open your browser and go to: [http://localhost:7474](http://localhost:7474)
   - Log in using the username and password you set in your `.env` file.

---

## 4. Using the Full MOOC Data

To use the full MOOC dataset instead of a subset:

1. **Edit the Dockerfile**
   - Uncomment the following line:
     ```dockerfile
     COPY data/mooc ./data/mooc
     ```
2. **Set the DATA_FOLDER environment variable**
   - In your `.env` file, set:
     ```env
     DATA_FOLDER=data/mooc
     ```
3. **Rebuild and restart Docker containers**
   ```sh
   docker compose up --build
   ```

Your application will now use the full MOOC data for seeding and analysis.

---

Enjoy exploring your knowledge graph!
