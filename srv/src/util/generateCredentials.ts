import { generateHash, generateUserID, registerUser } from "../auth";
import * as crypto from "crypto";
import { CREDENTIAL_SPLITTER } from "../scan";
import Axios from "axios";
import http from "http";

const axios = Axios;

const user = registerUser();
const username = "doxblek";
const password = "someVerySafePassword123";

// const key = crypto.scryptSync(user.userHash, "salt", 24);
// console.log(`Generate-Key: ${key.reduce((prev, curr) => prev + curr)}`);
// const iv = crypto.randomFillSync(new Uint8Array(16));
// const cipher = crypto.createCipheriv("aes-192-gcm", key, iv);
// cipher.setEncoding("base64");
// let encryptedCredentials = "";
// cipher.on("data", chunk => encryptedCredentials += chunk);
// cipher.on("end", () => console.log(`Finished encryption: ${encryptedCredentials}`));
// cipher.write(`${username}${CREDENTIAL_SPLITTER}${password}`);
// cipher.end();

// const iv = crypto.randomBytes(16);
const iv = Buffer.alloc(16);
const key = Buffer.from(user.userHash);
const cipher = crypto.createCipheriv("aes-256-cbc", key, iv);
let encryptedCredentials = cipher.update(`${username}${CREDENTIAL_SPLITTER}${password}`, "utf8", "base64");
encryptedCredentials += cipher.final("base64");
// const encryptedCredentials = cipher.final("base64");
console.log(`Finished encryption: ${encryptedCredentials}`);

require("../server");

(async () => {
    await axios.put("http://localhost:5000/updateCredentials", {
        userID: user.userID,
        encryptedCredentials
    });
    
    const data = {
        userID: user.userID,
        userHash: user.userHash
    };
    
    const body = JSON.stringify(data);
    
    const options = {
        hostname: "localhost",
        port: "5000",
        path: "/updateFromDualis",
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Content-Length": body.length
        }
    };

    const req = http.request(options, res => {
        res.on("data", d => console.log(new TextDecoder("utf-8").decode(d)));
    });

    req.on("error", console.log);

    req.write(body);
    req.end();
})();
