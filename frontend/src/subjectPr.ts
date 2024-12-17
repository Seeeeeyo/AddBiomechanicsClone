import Session from "./model/Session";
import SubjectViewState from "./model/SubjectViewState";
import UserHomeDirectory from "./model/UserHomeDirectory";
import { LiveDirectoryImpl } from "./model/LiveDirectory";
import { PubSubSocketMock } from "./model/PubSubSocket";
import { S3APIMock } from "./model/S3API";
// NodeJS imports

// Mock function to create a session
const createSession = () => {
    const s3Mock = new S3APIMock();
    const pubSubMock = new PubSubSocketMock("DEV");
    const session = new Session(s3Mock, pubSubMock, "us-west-2");
    session.setLoggedIn("testUser", "testUser@example.com");
    return session;
};

// Function to create a new subject
const createNewSubject = async (
    homeDirectory: UserHomeDirectory,
    subjectPath: string,
    subjectAttributes: any,
    markerFiles: File[]
) => {
    // Step 1: Initialize subject state
    const subjectState = homeDirectory.getSubjectViewState(subjectPath);

    // Step 2: Set subject attributes programmatically
    Object.keys(subjectAttributes).forEach((key) => {
        subjectState.subjectJson.setAttribute(key, subjectAttributes[key]);
    });

    // Step 3: Upload marker files
    markerFiles.forEach((file) => {
        subjectState.dropFilesToUpload([file]);
    });

    // Step 4: Submit for processing
    if (subjectState.canProcess()) {
        await subjectState.submitForProcessing();
        console.log("Subject data submitted for processing.");
    } else {
        console.error("Cannot submit subject for processing. Missing fields or data.");
    }
};

// Example usage
(async () => {
    // Step 1: Create a session
    const session = createSession();

    // Step 2: Access user home directory
    const url = session.parseDataURL("/data/test/newSubject");
    const homeDirectory = url.homeDirectory;

    // Step 3: Define subject attributes
    const subjectAttributes = {
        heightM: 1.75,
        massKg: 70,
        sex: "male",
        ageYears: 25,
        subjectTags: ["healthy", "athlete"],
        skeletonPreset: "vicon",
        disableDynamics: false,
        subjectConsent: true,
    };

    // Step 4: Prepare marker files
    const markerFile1 = new File(["marker data"], "trial1.trc", { type: "text/plain" });
    const markerFile2 = new File(["marker data"], "trial2.trc", { type: "text/plain" });

    // Step 5: Create new subject and upload data
    await createNewSubject(homeDirectory, url.path, subjectAttributes, [markerFile1, markerFile2]);
})();
