import assert from "assert";
import { generateHash } from "../src/auth";

describe("Auth Tests", () => {
    describe("Hash Generation", () => {
        it("Hash should have a length of 25", () => {
            const hash = generateHash();
            console.log(`Hash: ${hash}`);
            assert.equal(hash.length, 25);
        })
    });
});