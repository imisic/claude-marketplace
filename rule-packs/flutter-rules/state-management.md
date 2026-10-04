---
paths:
  - "**/*.dart"
---

# State Management

The examples use Riverpod (the stack this pack is drawn from), but the principles hold for Bloc or Provider too. The point is where state and logic live, not which package holds them.

## Principles
- Business logic lives in a notifier or repository layer, never in a widget's `build`.
- No global mutable state outside your state containers.
- Dispose resources. Lean on the framework's automatic disposal of unused state where it exists, and clean up anything it doesn't.
- Keep each unit of state small and focused.

## Reading State (Riverpod terms)
- Read once in callbacks and event handlers (`ref.read`); subscribe and rebuild in `build` (`ref.watch`); side effects without a rebuild via `ref.listen`.
- Don't create providers inside `build`. Declare them at top level.
- Use `select` to rebuild only on the slice you care about, and `family` for parameterized providers.

## Repository Pattern
- A repository wraps the data source; a provider exposes it. Screens depend on the provider, not the raw client.

```dart
final userRepositoryProvider = Provider((ref) => UserRepository(ref.watch(apiClientProvider)));
final usersProvider = FutureProvider((ref) => ref.watch(userRepositoryProvider).getUsers());
```

## Async States
- Branch on the async value for every data view: data, loading, and error, each handled. No screen that renders blank while a future is pending.

```dart
usersProvider.when(data: (u) => UserList(u), loading: () => const Spinner(), error: (e, st) => ErrorView(e));
```

## Testing
- Override providers inside a scope for tests instead of reaching for real network calls.
