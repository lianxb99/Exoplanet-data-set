CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -pthread
LDFLAGS = -lm -pthread

# Source files
SOURCES = 1553b_protocol.c 1553b_bus_controller.c 1553b_remote_terminal.c example_1553b_system.c
OBJECTS = $(SOURCES:.c=.o)

# Target executable
TARGET = 1553b_example

# Default target
all: $(TARGET)

# Build the executable
$(TARGET): $(OBJECTS)
	$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

# Compile source files
%.o: %.c 1553b_protocol.h
	$(CC) $(CFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -f $(OBJECTS) $(TARGET)

# Run the example
run: $(TARGET)
	./$(TARGET)

# Debug build
debug: CFLAGS += -g -DDEBUG
debug: $(TARGET)

# Release build
release: CFLAGS += -DNDEBUG
release: $(TARGET)

# Install dependencies (for Ubuntu/Debian)
install-deps:
	sudo apt-get update
	sudo apt-get install -y build-essential

# Check for memory leaks with valgrind
valgrind: $(TARGET)
	valgrind --leak-check=full --show-leak-kinds=all ./$(TARGET)

# Static analysis with cppcheck
cppcheck:
	cppcheck --enable=all --std=c99 *.c *.h

# Format code with clang-format
format:
	clang-format -i *.c *.h

.PHONY: all clean run debug release install-deps valgrind cppcheck format