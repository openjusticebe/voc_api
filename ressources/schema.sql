DROP INDEX IF EXISTS links_item_idx;
DROP INDEX IF EXISTS links_term_idx;
DROP INDEX IF EXISTS links_op_idx;


CREATE TABLE "links" (
    -- internal id
    id_internal SERIAL PRIMARY KEY,
    -- core table data
    item_iri TEXT,
    term_iri TEXT,
    -- operation ID
    op_uuid UUID,
    -- misc
    date_created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    date_updated TIMESTAMP WITH TIME ZONE
)

CREATE INDEX links_item_idx ON "links" (item_iri)
CREATE INDEX links_term_idx ON "links" (term_iri)
CREATE INDEX links_op_idx ON "links" USING GIST(op_uuid)
