# Getting Started

This project contains a seed script that will automatically insert all the necessary data into the knowledge graph when you start the application.

Follow these steps to set up and run the project:

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

Enjoy exploring your knowledge graph!
