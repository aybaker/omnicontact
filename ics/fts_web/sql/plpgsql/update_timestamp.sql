CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $update_timestamp$
  BEGIN
    NEW."UpdatedInDB" := LOCALTIMESTAMP(0);
    RETURN NEW;
  END;
$update_timestamp$ LANGUAGE plpgsql;
