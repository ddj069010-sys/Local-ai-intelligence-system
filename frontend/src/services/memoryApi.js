const API_BASE = "http://localhost:8000";

export const fetchMemoryEntries = async () => {
    try {
        const response = await fetch(`${API_BASE}/memory`);
        if (!response.ok) throw new Error("Failed to fetch memory entries");
        return await response.json();
    } catch (error) {
        console.error("fetchMemoryEntries Error:", error);
        return [];
    }
};

export const searchMemory = async (query) => {
    try {
        const response = await fetch(`${API_BASE}/memory/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("Search failed");
        return await response.json();
    } catch (error) {
        console.error("searchMemory Error:", error);
        return [];
    }
};

export const addMemoryEntry = async (entry) => {
    try {
        const response = await fetch(`${API_BASE}/memory`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entry)
        });
        if (!response.ok) throw new Error("Failed to add memory entry");
        return await response.json();
    } catch (error) {
        console.error("addMemoryEntry Error:", error);
        return { status: "error" };
    }
};

export const deleteMemoryEntry = async (id) => {
    try {
        const response = await fetch(`${API_BASE}/memory/${id}`, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Failed to delete memory entry");
        return await response.json();
    } catch (error) {
        console.error("deleteMemoryEntry Error:", error);
        return { status: "error" };
    }
};
