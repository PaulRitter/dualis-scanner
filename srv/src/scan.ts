import { CacheRecord, UserHash } from "./db/types";
import { authMockTable, cacheMockTable } from "./dbMock";
import * as crypto from "crypto";
import { exec } from "child_process";

export const CREDENTIAL_SPLITTER = "_+*CRED*+_";
const CACHE_EXPIRE_TIME = 15;

export function scan(userData: UserHash, res: any): void {
    const encryptedCredentials = authMockTable.find(record => record.userID === userData.userID)?.encryptedCredentials;
    if (!encryptedCredentials) {
        res.status(400).send("Given User does not exist.");
        return;
    }

    // Check if cache is still valid
    const cachedData = cacheMockTable.find(record => record.userID === userData.userID);
    if (!!cachedData && cachedData.cachedItems?.length > 0 && isCacheValid(cachedData)) {
        res.status(200).send({
            data: cachedData
        });
        return;
    }

    const { userHash: hash } = userData;
    
    const iv = Buffer.alloc(16);
    const key = Buffer.from(hash);
    const decipher = crypto.createDecipheriv("aes-256-cbc", key, iv);
    let decryptedCredentials = decipher.update(encryptedCredentials, "base64", "utf8");
    decryptedCredentials += decipher.final("utf8");
    console.log(`Finished decryption: ${decryptedCredentials}`);

    const [ username, password, ] = decryptedCredentials.split(CREDENTIAL_SPLITTER);
    // TODO: Run actual worker script
    exec(`dualis-scanner-worker ${process.env.DUALIS_USERNAME} ${process.env.DUALIS_PWD} --driver=${process.env.CHROMEDRIVER_PATH}/chromedriver --dry`, (err, stdout, stderr) => {
        console.log(stdout, stderr);
        console.log("Finished scanning");
    });

    // Mock
    const result: CacheRecord = {
        cachedItems: [],
        lastModifiedAt: new Date(),
        userID: userData.userID
    };
    if (!cachedData) {
        res.status(200).send({
            data: result,
            deltas: result
        });
        return;
    }

    const deltas = determineDeltas(result, cachedData);
    res.status(200).send({
        data: result,
        deltas
    });
}

function isCacheValid(cacheRecord: CacheRecord): boolean {
    const delta = Date.now() - cacheRecord.lastModifiedAt.valueOf();
    return delta < CACHE_EXPIRE_TIME * 60 * 1000; // Mins to millis
}

export function determineDeltas(result: CacheRecord, cache: CacheRecord): CacheRecord | undefined {
    const deltas: CacheRecord = {
        userID: result.userID,
        lastModifiedAt: new Date(),
        cachedItems: []
    };

    for(const item of result.cachedItems) {
        if (!cache.cachedItems.find(record => record == item)) {
            deltas.cachedItems.push(item);
        }
    }

    return deltas.cachedItems.length > 0 ? deltas : undefined;
}