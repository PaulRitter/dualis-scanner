import { randomUUID } from "crypto";
import { UserHash } from "./db/types";
import { authMockTable, userExists } from "./dbMock";

export function generateHash(): string {
    const symbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890";
    const hashLength = 32;

    let hash = "";
    for(let i = 0; i < hashLength; i++) {
        hash += symbols[Math.floor(Math.random() * symbols.length)];
    }

    return hash;
}

export function generateUserID(): string {
    let uuid = randomUUID();
    
    if (userExists(uuid)) {
        uuid = generateUserID();
    }

    return uuid;
}

export function registerUser(): UserHash {
    const userID = generateUserID();
    const userHash = generateHash();

    authMockTable.push({
        userID,
        encryptedCredentials: null
    });

    return {
        userID,
        userHash
    };
}

export function updateUserCredentials(userID: string, encryptedCredentials: string, res: any) {
    const userRecord = authMockTable.find(record => record.userID === userID);
    if (!userRecord) {
        res.status(400).send("Given user does not exist.");
        return;
    }
    userRecord.encryptedCredentials = encryptedCredentials;
    res.status(200).send("");
}