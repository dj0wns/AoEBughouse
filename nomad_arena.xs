// Code written by Alian713 with some modificationS
int create2D(int m = 0, int n = 0, int defaultValue = 0) {
    static int uid = 0;
    int arrayID = xsArrayCreateInt(m, -1, "name"+uid);
    uid++;
    for(i = 0; < m) {
        xsArraySetInt(arrayID, i, xsArrayCreateInt(n, defaultValue, ""+uid));
        uid++;
    }
    return (arrayID);
}

void set2D(int arrayID = -1, int m = -1, int n = -1, int value = 0) {
    int rowID = xsArrayGetInt(arrayID, m);
    xsArraySetInt(rowID, n, value);
}

int get2D(int arrayID = -1, int m = -1, int n = -1) {
    int rowID = xsArrayGetInt(arrayID, m);
    return (xsArrayGetInt(rowID, n));
}

int wallMap = -1;
int size = -1;
int playerMap = -1;

bool insideMap(int x = -1, int y = -1) {
    return (size != -1 && x >= 0 && y >= 0 && x < size && y < size);
}

void setWalls(int x = -1, int y = -1, int p = -1) {
    const int wallRadius = 15; // if you want, you can use the map size to determine this dynamically
    // Make sure this matches the modulus in the generation script!
    // There is no modulus so just take advantage of int truncation.
    x = 3 * (x / 3);
    y = 3 * (y / 3);
    for(i = x-wallRadius; < x+wallRadius) {
        if(insideMap(i, y-wallRadius))
            set2D(wallMap, i, y-wallRadius, p);
        if(insideMap(i, y+wallRadius))
            set2D(wallMap, i, y+wallRadius, p);
    }
    for(j = y-wallRadius; < y+wallRadius) {
        if(insideMap(x-wallRadius, j))
            set2D(wallMap, x-wallRadius, j, p);
        if(insideMap(x+wallRadius, j))
            set2D(wallMap, x+wallRadius, j, p);
    }
    xsArraySetInt(playerMap, p, 0);
}

void main() {
    size = xsGetMapWidth();
    wallMap = create2D(size, size, -1);
    playerMap = xsArrayCreateInt(8, -1, "players");
}

bool isWall(int x = -1, int y = -1, int p = -1) {
    return (get2D(wallMap, x, y) == p);
}

bool didPlayerBuildTC(int p = -1) {
    return (xsArrayGetInt(playerMap, p) == 1);
}

bool didPlayerCompleteTC(int p = -1) {
    bool result = (xsArrayGetInt(playerMap, p) == 0);
    if (result)
      xsArraySetInt(playerMap, p, 1);
    return (result);
}


