# Stack adapters

Adapters detect capabilities; they do not impose a stack. Detection must be based on repository evidence such as manifests, lockfiles, configuration, and runnable scripts.

The Laravel adapter detects `artisan`, `composer.json`, framework versions, and `laravel/boost`. Boost remains optional and approval-gated. A future Power Design System adapter may provide design references without changing the core workflow layout.
