#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  DNS Debugger (d) - Installation Script  ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dog (DNS client)
install_dog() {
    print_info "Checking for dog (modern DNS client)..."

    if command_exists dog; then
        print_success "dog is already installed"
        return 0
    fi

    print_warning "dog not found, attempting to install..."

    if [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install dog
            print_success "dog installed via Homebrew"
        else
            print_warning "Homebrew not found. Please install dog manually: https://dns.lookup.dog/"
        fi
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y dog
            print_success "dog installed via apt"
        elif command_exists dnf; then
            sudo dnf install -y dog
            print_success "dog installed via dnf"
        elif command_exists pacman; then
            sudo pacman -S --noconfirm dog
            print_success "dog installed via pacman"
        else
            print_warning "Package manager not recognized. Please install dog manually: https://dns.lookup.dog/"
        fi
    else
        print_warning "Automatic installation not supported for $OS. Will fallback to dig."
    fi
}

# Check for dig (fallback)
check_dig() {
    print_info "Checking for dig (DNS fallback)..."

    if command_exists dig; then
        print_success "dig is available as fallback"
    else
        print_warning "dig not found. Please install bind-tools/dnsutils"
    fi
}

# Check for OpenSSL
check_openssl() {
    print_info "Checking for openssl..."

    if command_exists openssl; then
        print_success "openssl is available"
    else
        print_error "openssl not found. Please install OpenSSL"
        exit 1
    fi
}

# Install Python dependencies
install_python_deps() {
    print_info "Checking Python installation..."

    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"

    # Check for pipx
    if ! command_exists pipx; then
        print_info "Installing pipx..."
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
        print_success "pipx installed"
    else
        print_success "pipx is already installed"
    fi
}

# Install the d command
install_d() {
    print_info "Installing d (DNS Debugger)..."

    if command_exists pipx; then
        pipx install d-dns-debugger
        print_success "d installed successfully"
    else
        print_error "pipx installation failed. Trying pip..."
        python3 -m pip install --user d-dns-debugger
        print_success "d installed via pip"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    if command_exists d; then
        VERSION=$(d --version 2>&1 || echo "unknown")
        print_success "d command is available: $VERSION"
        return 0
    else
        print_warning "d command not found in PATH. You may need to restart your shell or add ~/.local/bin to your PATH"
        print_info "Add this to your ~/.bashrc or ~/.zshrc:"
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        return 1
    fi
}

# Main installation flow
main() {
    print_header

    detect_os
    print_info "Detected OS: $OS"

    # Install dependencies
    install_dog
    check_dig
    check_openssl
    install_python_deps

    # Install the application
    install_d

    # Verify
    echo ""
    if verify_installation; then
        echo ""
        print_success "Installation complete! 🎉"
        echo ""
        print_info "Try it out:"
        echo "    d example.com"
        echo ""
    else
        echo ""
        print_warning "Installation completed with warnings. Please check the messages above."
        echo ""
    fi
}

# Run main function
main
