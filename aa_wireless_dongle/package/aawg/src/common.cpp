#include <cstdlib>
#include <cstdarg>
#include <sstream>
#include <fstream>
#include <cctype>
#include <syslog.h>

#include "common.h"
#include "proto/WifiInfoResponse.pb.h"

#pragma region Config
/*static*/ Config* Config::instance() {
    static Config s_instance;
    return &s_instance;
}

int32_t Config::getenv(std::string name, int32_t defaultValue) {
    char* envValue = std::getenv(name.c_str());
    try {
        return envValue != nullptr ? std::stoi(envValue) : defaultValue;
    }
    catch(...) {
        return defaultValue;
    }
}

std::string Config::getenv(std::string name, std::string defaultValue) {
    char* envValue = std::getenv(name.c_str());
    return envValue != nullptr ? envValue : defaultValue;
}

std::string Config::getMacAddress(std::string interface) {
    std::ifstream addressFile("/sys/class/net/" + interface + "/address");

    std::string macAddress;
    if (!addressFile.is_open()) {
        Logger::instance()->info("Unable to read MAC address for interface %s\n", interface.c_str());
        return "";
    }

    getline(addressFile, macAddress);

    if (macAddress.empty()) {
        Logger::instance()->info("MAC address for interface %s is empty\n", interface.c_str());
    }

    return macAddress;
}

std::string Config::getWifiInterface() {
    return getenv("AAWG_WIFI_INTERFACE", "wlan0");
}

std::string Config::getFallbackBssid() {
    std::string suffix = getUniqueSuffix();
    std::string hexDigits;
    for (char ch : suffix) {
        if (std::isxdigit(static_cast<unsigned char>(ch))) {
            hexDigits.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
        }
    }

    if (hexDigits.size() < 6) {
        hexDigits.insert(hexDigits.begin(), 6 - hexDigits.size(), '0');
    } else if (hexDigits.size() > 6) {
        hexDigits = hexDigits.substr(hexDigits.size() - 6);
    }

    std::string bssid = "02:00:";
    bssid += hexDigits.substr(0, 2);
    bssid += ":";
    bssid += hexDigits.substr(2, 2);
    bssid += ":";
    bssid += hexDigits.substr(4, 2);
    return bssid;
}

std::string Config::getUniqueSuffix() {
    std::string uniqueSuffix = getenv("AAWG_UNIQUE_NAME_SUFFIX", "");
    if (!uniqueSuffix.empty()) {
        return uniqueSuffix;
    }

    std::ifstream serialNumberFile("/sys/firmware/devicetree/base/serial-number");

    std::string serialNumber;
    getline(serialNumberFile, serialNumber);

    // Removing trailing null from serialNumber, pad at the beginning
    serialNumber = std::string("00000000") + serialNumber.c_str();

    return serialNumber.substr(serialNumber.size() - 6);
}

WifiInfo Config::getWifiInfo() {
    std::string bssid = getenv("AAWG_WIFI_BSSID", "");
    if (bssid.empty()) {
        std::string interface = getWifiInterface();
        bssid = getMacAddress(interface);
        if (bssid.empty()) {
            bssid = getFallbackBssid();
            Logger::instance()->info("Using fallback BSSID %s\n", bssid.c_str());
        }
    }

    return {
        getenv("AAWG_WIFI_SSID", "AAWirelessDongle"),
        getenv("AAWG_WIFI_PASSWORD", "ConnectAAWirelessDongle"),
        bssid,
        SecurityMode::WPA2_PERSONAL,
        AccessPointType::DYNAMIC,
        getenv("AAWG_PROXY_IP_ADDRESS", "10.0.0.1"),
        getenv("AAWG_PROXY_PORT", 5288),
    };
}

ConnectionStrategy Config::getConnectionStrategy() {
    if (!connectionStrategy.has_value()) {
        const int32_t connectionStrategyEnv = getenv("AAWG_CONNECTION_STRATEGY", 1);

        switch (connectionStrategyEnv) {
            case 0:
                connectionStrategy = ConnectionStrategy::DONGLE_MODE;
                break;
            case 1:
                connectionStrategy = ConnectionStrategy::PHONE_FIRST;
                break;
            case 2:
                connectionStrategy = ConnectionStrategy::USB_FIRST;
                break;
            default:
                connectionStrategy = ConnectionStrategy::PHONE_FIRST;
                break;
        }
    }

    return connectionStrategy.value();
}
#pragma endregion Config

#pragma region Logger
/*static*/ Logger* Logger::instance() {
    static Logger s_instance;
    return &s_instance;
}

Logger::Logger() {
    openlog(nullptr, LOG_PERROR | LOG_PID, LOG_USER);
}

Logger::~Logger() {
    closelog();
}

void Logger::info(const char *format, ...) {
    va_list args;
    va_start(args, format);
    vsyslog(LOG_INFO, format, args);
    va_end(args);
}
#pragma endregion Logger
