# Rebuild RECIPE for fixtures/data.json

Follow these steps **in order**. Do not skip any step. Do not reorder.

1. Create the directory `fixtures/` if it does not exist.

2. Read the file `inputs/users.csv`. It contains user rows in the
   format: `id,name,email`.

3. Read the file `inputs/orders.csv`. It contains order rows in the
   format: `order_id,user_id,total_cents`.

4. Build a JSON object with two top-level keys:
     - `users`: an array of objects with keys `id` (int), `name` (str),
       `email` (str), in the order they appear in users.csv.
     - `orders`: an array of objects with keys `order_id` (int),
       `user_id` (int), `total_cents` (int), in the order they appear
       in orders.csv.

5. Write the JSON to `fixtures/data.json` with **2-space indentation**
   and a trailing newline.

6. Append a single line to `BUILD.log` (creating it if necessary) with
   the exact text: `fixture rebuilt`. No timestamp, no prefix.
