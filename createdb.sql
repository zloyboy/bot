create table if not exists user(
    id integer primary key,
    created datetime,
    name varchar(255),
    age integer,
    res integer
);

create index if not exists age_index on user (age);
