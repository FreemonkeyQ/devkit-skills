# orders service

- Build: `mvn -q -DskipTests package`
- Test: `mvn test`
- Migrations: `src/main/resources/db/migration`
- API responses are records under `src/main/java/com/example/orders/api`.
- Use constructor injection; do not add Lombok.
- Tests use JUnit 5 with AssertJ and Mockito.
