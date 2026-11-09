#include <iostream>
#include <cassert>

// Forward declaration so the compiler knows add() exists
int add(int a, int b);

void test_add() {
    assert(add(2, 3) == 5); 
}

// We add a main function here so g++ has a starting point to run the executable
int main() {
    test_add();
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
