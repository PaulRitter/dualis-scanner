import { generateUserID } from "./auth";
import { AuthRecord, CacheItem, CacheRecord } from "./db/types";

const authMockTable: AuthRecord[] = [
    {
        userID: "someUserID",
        encryptedCredentials: "foo"
    }
];

const cacheMockTable: CacheRecord[] = [
    {
        lastModifiedAt: new Date(),
        userID: "someUserID",
        cachedItems: []
    }
]

export function userExists(userID: string): boolean {
    return authMockTable.find(record => record.userID === userID) != undefined;
}

export {authMockTable, cacheMockTable};