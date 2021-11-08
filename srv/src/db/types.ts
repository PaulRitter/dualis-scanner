export interface AuthRecord {
    userID: string;
    encryptedCredentials: string | null
};

export interface CacheRecord {
    userID: string;
    cachedItems: CacheItem[];
    lastModifiedAt: Date;
};

export interface CacheItem {
    lecture: String;
    grade: number;
    semester: number;
};

export interface UserHash {
    userID: string;
    userHash: string;
};