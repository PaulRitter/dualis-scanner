import express from "express";
import { registerUser, updateUserCredentials } from "./auth";
import bodyParser from "body-parser";
import { authMockTable } from "./dbMock";
import { UserHash } from "./db/types";
import { scan } from "./scan";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.PORT ?? 5000;

const app = express();

app.use(bodyParser.json({
}));

app.get("/", (req, res) => res.send("Welcome in the Dualis-Scanner-Backend!"));

app.post("/register", (req, res) => {
    const authHash = registerUser();
    res.status(201).send(authHash);
});

app.put("/updateCredentials", (req, res) => {
    const { userID, encryptedCredentials } = (req as any).body;
    updateUserCredentials(userID, encryptedCredentials, res);
});

app.get("/authTable", (req, res) => {
    res.send(authMockTable);
});

app.get("/updateFromDualis", (req, res) => {
    const userData: UserHash = req.body;
    scan(userData, res);
})

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}...`);
});