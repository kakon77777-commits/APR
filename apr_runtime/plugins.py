from __future__ import annotations

from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Callable, Dict, Mapping, Protocol, Tuple, runtime_checkable

PLUGIN_ENTRY_POINT_GROUP = "apr_runtime.plugins"
ComponentFactory = Callable[..., Any]


class PluginError(RuntimeError):
    """Base error for APR plugin registration and loading."""


class DuplicateComponentError(PluginError):
    """Raised when a plugin attempts to replace a component implicitly."""


class PluginLoadError(PluginError):
    """Raised for an entry-point load failure in strict mode."""


@runtime_checkable
class APRPlugin(Protocol):
    """Minimal contract implemented by an APR runtime plugin."""

    name: str

    def register(self, registry: "PluginRegistry") -> None:
        """Register component factories without starting external resources."""


@dataclass(frozen=True)
class LoadedPlugin:
    entry_point: str
    plugin_name: str


@dataclass(frozen=True)
class PluginFailure:
    entry_point: str
    error: str


@dataclass
class PluginLoadReport:
    loaded: list[LoadedPlugin] = field(default_factory=list)
    failures: list[PluginFailure] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


class PluginRegistry:
    """
    Explicit registry for trusted APR extensions.

    Loading is opt-in because Python entry points execute third-party code.
    A failed plugin installation is transactional: component registrations made
    by that plugin are rolled back before the error is reported.
    """

    def __init__(self) -> None:
        self._components: Dict[str, Dict[str, ComponentFactory]] = {}
        self._plugins: Dict[str, APRPlugin] = {}

    @staticmethod
    def _name(label: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must be a non-empty string")
        return value.strip()

    def register_component(
        self,
        kind: str,
        name: str,
        factory: ComponentFactory,
        *,
        replace: bool = False,
    ) -> None:
        kind = self._name("kind", kind)
        name = self._name("name", name)
        if not callable(factory):
            raise TypeError("factory must be callable")

        bucket = self._components.setdefault(kind, {})
        if name in bucket and not replace:
            raise DuplicateComponentError(f"component {kind!r}/{name!r} is already registered")
        bucket[name] = factory

    def component_factory(self, kind: str, name: str) -> ComponentFactory:
        try:
            return self._components[kind][name]
        except KeyError as exc:
            raise KeyError(f"unknown APR component {kind!r}/{name!r}") from exc

    def create_component(self, kind: str, name: str, /, *args: Any, **kwargs: Any) -> Any:
        return self.component_factory(kind, name)(*args, **kwargs)

    def components(self, kind: str | None = None) -> Mapping[str, Any]:
        if kind is not None:
            return dict(self._components.get(kind, {}))
        return {key: dict(value) for key, value in self._components.items()}

    @property
    def plugin_names(self) -> Tuple[str, ...]:
        return tuple(self._plugins)

    def install(self, plugin: APRPlugin) -> None:
        if not isinstance(plugin, APRPlugin):
            raise TypeError("plugin must provide a name and register(registry) method")
        name = self._name("plugin.name", plugin.name)
        if name in self._plugins:
            raise PluginError(f"plugin {name!r} is already installed")

        snapshot = {kind: dict(values) for kind, values in self._components.items()}
        try:
            plugin.register(self)
        except Exception:
            self._components = snapshot
            raise
        self._plugins[name] = plugin

    def load_entry_points(
        self,
        *,
        group: str = PLUGIN_ENTRY_POINT_GROUP,
        strict: bool = False,
    ) -> PluginLoadReport:
        report = PluginLoadReport()
        for entry_point in metadata.entry_points(group=group):
            try:
                candidate = entry_point.load()
                plugin = candidate() if isinstance(candidate, type) else candidate
                self.install(plugin)
                report.loaded.append(LoadedPlugin(entry_point.name, plugin.name))
            except Exception as exc:
                failure = PluginFailure(entry_point.name, f"{type(exc).__name__}: {exc}")
                report.failures.append(failure)
                if strict:
                    raise PluginLoadError(
                        f"failed to load APR plugin {entry_point.name!r}: {exc}"
                    ) from exc
        return report
