from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import load
from conan.tools.env import VirtualBuildEnv
import re
from os import path


class ConcoreRecipe(ConanFile):
    name = "concore"
    description = "Core abstractions for dealing with concurrency in C++"
    author = "Lucian Radu Teodorescu"
    topics = ("concurrency", "tasks", "executors", "no-locks")
    homepage = "https://github.com/lucteo/concore"
    url = "https://github.com/lucteo/concore"
    license = "MIT"

    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    # We export the license and all source files needed to build
    exports_sources = ("src/*", "include/*", "CMakeLists.txt", "LICENSE")

    # We no longer use the old "cmake" generator
    # build_policy = "missing"  → no longer needed in Conan 2 (handled by --build)

    def set_version(self):
        # Extract version from src/CMakeLists.txt
        cmake_content = load(self, path.join(self.recipe_folder, "src", "CMakeLists.txt"))
        match = re.search(r"project\([^\)]+VERSION (\d+\.\d+\.\d+)[^\)]*\)", cmake_content)
        if match:
            self.version = match.group(1).strip()
        else:
            raise ValueError("Could not extract version from CMakeLists.txt")

    @property
    def _run_tests(self):
        # You can control this via environment variable or profile
        return self.conf.get("user.concore:run_tests", False, check_type=bool)

    def requirements(self):
        # Put runtime dependencies here (none in your original)
        pass

    def build_requirements(self):
        if self._run_tests:
            self.build_requires("catch2/3.8.0")          # updated to newer version
            self.build_requires("rapidcheck/cci.20230524")  # use latest available
            self.build_requires("benchmark/1.9.0")      # updated

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)

        # Preserve your special handling for shared libs on Windows
        if self.settings.compiler == "msvc" and self.options.shared:
            tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True

        # You can add more variables if needed
        # tc.variables["SOME_OPTION"] = "ON"

        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        # Optional: if you need build environment variables
        VirtualBuildEnv(self).generate(scope="build")

    def build(self):
        cmake = CMake(self)

        # In Conan 2, source_folder is handled by layout
        # We build the whole project (including tests if dependencies are present)
        cmake.configure()

        cmake.build()

        # Optional: run tests during build if desired
        # if self._run_tests:
        #     cmake.test()

    def package(self):
        # Copy license
        self.copy("LICENSE", dst="licenses")

        # Install using CMake (this runs `cmake --install`)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # Conan 2 style — collect libraries automatically
        self.cpp_info.libs = self.cpp_info.collect_libs()

        # If needed you can be more explicit:
        # self.cpp_info.components["concore"].libs = ["concore"]
