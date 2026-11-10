--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: notes_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.notes_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.searchable := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;




--
-- Name: ai_costs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_costs (
    id integer NOT NULL,
    interaction_type character varying(50) NOT NULL,
    provider character varying(50) NOT NULL,
    model character varying(100),
    prompt_tokens integer DEFAULT 0 NOT NULL,
    completion_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer DEFAULT 0 NOT NULL,
    cost_usd numeric(12,8) DEFAULT 0 NOT NULL,
    generation_time_s double precision,
    report_id integer,
    meeting_id integer,
    context_label character varying(255),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    thinking_tokens integer,
    refused boolean DEFAULT false NOT NULL,
    finish_reason character varying(50)
);


--
-- Name: ai_costs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_costs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_costs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_costs_id_seq OWNED BY public.ai_costs.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    name text NOT NULL,
    is_active boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    slack_channel text,
    CONSTRAINT clients_name_not_internal CHECK ((lower(name) <> 'internal'::text))
);


--
-- Name: TABLE clients; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.clients IS 'Client records. is_active=TRUE identifies the active client. Only one row may have is_active=TRUE at a time (repository-enforced). NULL client_id on data records = internal/company work. The reserved keyword internal on clients set active clears context. A client named internal cannot be created (CHECK constraint + functional unique index on lower(name)).';


--
-- Name: COLUMN clients.slack_channel; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.clients.slack_channel IS 'Slack channel for this client (e.g. #client-channel). NULL = use config.json default_channel as fallback. Set via: workmain slack set channel <channel>.';


--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: gdrive_uploads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gdrive_uploads (
    id integer NOT NULL,
    local_path text NOT NULL,
    drive_file_id text NOT NULL,
    drive_folder_id text NOT NULL,
    filename text NOT NULL,
    upload_type text NOT NULL,
    upload_date date NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: gdrive_uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.gdrive_uploads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: gdrive_uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.gdrive_uploads_id_seq OWNED BY public.gdrive_uploads.id;


--
-- Name: meetings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meetings (
    id integer NOT NULL,
    outlook_id character varying(255),
    outlook_recurring_id character varying(255),
    title character varying(255) NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone NOT NULL,
    attendees text[],
    is_recurring boolean DEFAULT false,
    notes_captured boolean DEFAULT false,
    reminder_sent boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    condensed_summary text,
    condensed_at timestamp without time zone,
    is_manually_modified boolean DEFAULT false NOT NULL,
    is_cancelled boolean DEFAULT false NOT NULL,
    client_id integer
);


--
-- Name: COLUMN meetings.condensed_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.meetings.condensed_summary IS 'AI-generated one-line summary of all meeting notes for Clockify time entry';


--
-- Name: COLUMN meetings.condensed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.meetings.condensed_at IS 'Timestamp when AI condensation was performed';


--
-- Name: COLUMN meetings.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.meetings.client_id IS 'NULL = internal/company work. Non-NULL = attributed client.';


--
-- Name: meetings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.meetings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: meetings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.meetings_id_seq OWNED BY public.meetings.id;


--
-- Name: notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notes (
    id integer NOT NULL,
    project_id integer,
    meeting_id integer,
    content text NOT NULL,
    tags text[],
    source character varying(50),
    created_at timestamp without time zone DEFAULT now(),
    created_date date GENERATED ALWAYS AS ((created_at)::date) STORED,
    updated_at timestamp without time zone DEFAULT now(),
    searchable tsvector,
    client_id integer
);


--
-- Name: COLUMN notes.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.notes.client_id IS 'NULL = internal/company work. Non-NULL = attributed client.';


--
-- Name: notes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notes_id_seq OWNED BY public.notes.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    client_id integer,
    name character varying(255) NOT NULL,
    description text,
    status character varying(50) DEFAULT 'active'::character varying,
    clockify_project_id character varying(255),
    start_date date,
    end_date date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: recipients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipients (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: recipients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recipients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recipients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recipients_id_seq OWNED BY public.recipients.id;


--
-- Name: report_recipients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.report_recipients (
    id integer NOT NULL,
    report_type character varying(50) NOT NULL,
    recipient_type character varying(10) NOT NULL,
    client_id integer,
    created_at timestamp without time zone DEFAULT now(),
    recipient_id integer
);


--
-- Name: COLUMN report_recipients.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.report_recipients.client_id IS 'NULL = global recipient (appears in all client email drafts). Non-NULL = scoped to the specified client only. Set implicitly by email assign based on active client context.';


--
-- Name: report_recipients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.report_recipients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: report_recipients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.report_recipients_id_seq OWNED BY public.report_recipients.id;


--
-- Name: reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reports (
    id integer NOT NULL,
    report_type character varying(50) NOT NULL,
    report_date date NOT NULL,
    content text NOT NULL,
    metadata jsonb,
    validation_passed boolean,
    sent_at timestamp without time zone,
    outlook_draft_id character varying(255),
    slack_message_ts character varying(255),
    created_at timestamp without time zone DEFAULT now(),
    slack_channel text,
    slack_workspace_name text,
    client_id integer,
    status character varying(20) DEFAULT 'unconfirmed'::character varying NOT NULL,
    corrected_content text,
    correction_note text,
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT reports_status_check CHECK (status IN ('unconfirmed', 'confirmed', 'corrected'))
);


--
-- Name: COLUMN reports.slack_message_ts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reports.slack_message_ts IS 'Slack message timestamp (ts). Non-null = report was posted to Slack.';


--
-- Name: COLUMN reports.slack_channel; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reports.slack_channel IS 'Slack channel the report was posted to (e.g. #weekly-reports).';


--
-- Name: COLUMN reports.slack_workspace_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reports.slack_workspace_name IS 'Human-readable Slack workspace name cached from auth.test at time of post.';


--
-- Name: COLUMN reports.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.reports.client_id IS 'NULL = internal/company work. Non-NULL = attributed client.';


--
-- Name: reports_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reports_id_seq OWNED BY public.reports.id;


--
-- Name: schedule_exceptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule_exceptions (
    id integer NOT NULL,
    type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    name text,
    reason text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT end_after_start CHECK ((end_date >= start_date)),
    CONSTRAINT schedule_exceptions_type_check CHECK (type IN ('holiday', 'timeoff'))
);


--
-- Name: TABLE schedule_exceptions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.schedule_exceptions IS 'Calendar exceptions that suppress daemon notifications. type=holiday for named holidays; type=timeoff for personal time off.';


--
-- Name: schedule_exceptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schedule_exceptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schedule_exceptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schedule_exceptions_id_seq OWNED BY public.schedule_exceptions.id;


--
-- Name: system_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_state (
    key character varying(100) NOT NULL,
    value text,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: TABLE system_state; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.system_state IS 'General-purpose KV store for WorkmAIn runtime state. String values only — repository layer handles type casting. Keys: notify_method, notify_enabled, active_client_id.';


--
-- Name: task_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_status (
    id integer NOT NULL,
    note_id integer NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    completed_at timestamp without time zone,
    forwarding_note_id integer,
    CONSTRAINT task_status_status_check CHECK (status IN ('active', 'completed', 'dismissed'))
);


--
-- Name: task_status_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_status_id_seq OWNED BY public.task_status.id;


--
-- Name: time_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.time_entries (
    id integer NOT NULL,
    project_id integer,
    duration_hours numeric(5,2) NOT NULL,
    category character varying(100),
    clockify_id character varying(255),
    entry_date date NOT NULL,
    entry_time time without time zone NOT NULL,
    synced_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    meeting_id integer,
    client_id integer,
    note_id integer NOT NULL
);


--
-- Name: COLUMN time_entries.meeting_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.time_entries.meeting_id IS 'Foreign key to meetings table - links Clockify time entry to source meeting';


--
-- Name: COLUMN time_entries.client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.time_entries.client_id IS 'NULL = internal/company work. Non-NULL = attributed client.';


--
-- Name: time_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.time_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: time_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.time_entries_id_seq OWNED BY public.time_entries.id;


--
-- Name: ai_costs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_costs ALTER COLUMN id SET DEFAULT nextval('public.ai_costs_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Name: gdrive_uploads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gdrive_uploads ALTER COLUMN id SET DEFAULT nextval('public.gdrive_uploads_id_seq'::regclass);


--
-- Name: meetings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meetings ALTER COLUMN id SET DEFAULT nextval('public.meetings_id_seq'::regclass);


--
-- Name: notes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notes ALTER COLUMN id SET DEFAULT nextval('public.notes_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: recipients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients ALTER COLUMN id SET DEFAULT nextval('public.recipients_id_seq'::regclass);


--
-- Name: report_recipients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_recipients ALTER COLUMN id SET DEFAULT nextval('public.report_recipients_id_seq'::regclass);


--
-- Name: reports id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports ALTER COLUMN id SET DEFAULT nextval('public.reports_id_seq'::regclass);


--
-- Name: schedule_exceptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_exceptions ALTER COLUMN id SET DEFAULT nextval('public.schedule_exceptions_id_seq'::regclass);


--
-- Name: task_status id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_status ALTER COLUMN id SET DEFAULT nextval('public.task_status_id_seq'::regclass);


--
-- Name: time_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries ALTER COLUMN id SET DEFAULT nextval('public.time_entries_id_seq'::regclass);


--
-- Name: ai_costs ai_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_costs
    ADD CONSTRAINT ai_costs_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: gdrive_uploads gdrive_uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gdrive_uploads
    ADD CONSTRAINT gdrive_uploads_pkey PRIMARY KEY (id);


--
-- Name: meetings meetings_outlook_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meetings
    ADD CONSTRAINT meetings_outlook_id_key UNIQUE (outlook_id);


--
-- Name: meetings meetings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meetings
    ADD CONSTRAINT meetings_pkey PRIMARY KEY (id);


--
-- Name: notes notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_pkey PRIMARY KEY (id);


--
-- Name: projects projects_client_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_client_id_name_key UNIQUE (client_id, name);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: recipients recipients_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_email_key UNIQUE (email);


--
-- Name: recipients recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_pkey PRIMARY KEY (id);


--
-- Name: report_recipients report_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_recipients
    ADD CONSTRAINT report_recipients_pkey PRIMARY KEY (id);


--
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);


--
-- Name: schedule_exceptions schedule_exceptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_exceptions
    ADD CONSTRAINT schedule_exceptions_pkey PRIMARY KEY (id);


--
-- Name: system_state system_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_state
    ADD CONSTRAINT system_state_pkey PRIMARY KEY (key);


--
-- Name: task_status task_status_note_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_status
    ADD CONSTRAINT task_status_note_id_key UNIQUE (note_id);


--
-- Name: task_status task_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_status
    ADD CONSTRAINT task_status_pkey PRIMARY KEY (id);


--
-- Name: time_entries time_entries_clockify_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_clockify_id_key UNIQUE (clockify_id);


--
-- Name: time_entries time_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_costs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_costs_created_at ON public.ai_costs USING btree (created_at);


--
-- Name: idx_ai_costs_interaction_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_costs_interaction_type ON public.ai_costs USING btree (interaction_type);


--
-- Name: idx_ai_costs_meeting_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_costs_meeting_id ON public.ai_costs USING btree (meeting_id);


--
-- Name: idx_ai_costs_provider; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_costs_provider ON public.ai_costs USING btree (provider);


--
-- Name: idx_ai_costs_report_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_costs_report_id ON public.ai_costs USING btree (report_id);


--
-- Name: idx_clients_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_clients_is_active ON public.clients USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_clients_name_ci_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_clients_name_ci_unique ON public.clients USING btree (lower(name));


--
-- Name: idx_gdrive_uploads_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gdrive_uploads_date ON public.gdrive_uploads USING btree (upload_date);


--
-- Name: idx_gdrive_uploads_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gdrive_uploads_type ON public.gdrive_uploads USING btree (upload_type);


--
-- Name: idx_meetings_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meetings_client_id ON public.meetings USING btree (client_id);


--
-- Name: idx_meetings_recurring; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meetings_recurring ON public.meetings USING btree (outlook_recurring_id);


--
-- Name: idx_meetings_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meetings_start ON public.meetings USING btree (start_time);


--
-- Name: idx_meetings_title_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meetings_title_trgm ON public.meetings USING gin (title public.gin_trgm_ops);


--
-- Name: idx_notes_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_client_id ON public.notes USING btree (client_id);


--
-- Name: idx_notes_content_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_content_trgm ON public.notes USING gin (content public.gin_trgm_ops);


--
-- Name: idx_notes_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_date ON public.notes USING btree (created_date);


--
-- Name: idx_notes_meeting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_meeting ON public.notes USING btree (meeting_id);


--
-- Name: idx_notes_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_search ON public.notes USING gin (searchable);


--
-- Name: idx_notes_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notes_tags ON public.notes USING gin (tags);


--
-- Name: idx_projects_client; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_client ON public.projects USING btree (client_id);


--
-- Name: idx_report_recipients_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_recipients_client_id ON public.report_recipients USING btree (client_id);


--
-- Name: idx_report_recipients_recipient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_report_recipients_recipient_id ON public.report_recipients USING btree (recipient_id);


--
-- Name: idx_reports_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_client_id ON public.reports USING btree (client_id);


--
-- Name: idx_reports_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_date ON public.reports USING btree (report_date);


--
-- Name: idx_reports_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_type ON public.reports USING btree (report_type);


--
-- Name: idx_schedule_exceptions_range; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_exceptions_range ON public.schedule_exceptions USING btree (start_date, end_date);


--
-- Name: idx_time_entries_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_client_id ON public.time_entries USING btree (client_id);


--
-- Name: idx_time_entries_clockify; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_clockify ON public.time_entries USING btree (clockify_id);


--
-- Name: idx_time_entries_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_date ON public.time_entries USING btree (entry_date);


--
-- Name: idx_time_entries_meeting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_meeting ON public.time_entries USING btree (meeting_id);


--
-- Name: idx_time_entries_meeting_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_meeting_id ON public.time_entries USING btree (meeting_id) WHERE (meeting_id IS NOT NULL);


--
-- Name: idx_time_entries_note_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_time_entries_note_id ON public.time_entries USING btree (note_id);


--
-- Name: ix_task_status_note_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_status_note_id ON public.task_status USING btree (note_id);


--
-- Name: ix_task_status_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_status_status ON public.task_status USING btree (status);


--
-- Name: notes notes_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER notes_search_update BEFORE INSERT OR UPDATE ON public.notes FOR EACH ROW EXECUTE FUNCTION public.notes_search_trigger();


--
-- Name: notes update_notes_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON public.notes FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: projects update_projects_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: time_entries update_time_entries_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_time_entries_updated_at BEFORE UPDATE ON public.time_entries FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: ai_costs ai_costs_meeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_costs
    ADD CONSTRAINT ai_costs_meeting_id_fkey FOREIGN KEY (meeting_id) REFERENCES public.meetings(id) ON DELETE SET NULL;


--
-- Name: ai_costs ai_costs_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_costs
    ADD CONSTRAINT ai_costs_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id) ON DELETE SET NULL;


--
-- Name: projects fk_projects_client_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT fk_projects_client_id FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: report_recipients fk_report_recipients_client_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_recipients
    ADD CONSTRAINT fk_report_recipients_client_id FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: meetings meetings_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meetings
    ADD CONSTRAINT meetings_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: notes notes_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: notes notes_meeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_meeting_id_fkey FOREIGN KEY (meeting_id) REFERENCES public.meetings(id) ON DELETE SET NULL;


--
-- Name: notes notes_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: report_recipients report_recipients_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_recipients
    ADD CONSTRAINT report_recipients_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.recipients(id) ON DELETE CASCADE;


--
-- Name: reports reports_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: task_status task_status_forwarding_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_status
    ADD CONSTRAINT task_status_forwarding_note_id_fkey FOREIGN KEY (forwarding_note_id) REFERENCES public.notes(id);


--
-- Name: task_status task_status_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_status
    ADD CONSTRAINT task_status_note_id_fkey FOREIGN KEY (note_id) REFERENCES public.notes(id) ON DELETE CASCADE;


--
-- Name: time_entries time_entries_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: time_entries time_entries_meeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_meeting_id_fkey FOREIGN KEY (meeting_id) REFERENCES public.meetings(id) ON DELETE SET NULL;


--
-- Name: time_entries time_entries_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_note_id_fkey FOREIGN KEY (note_id) REFERENCES public.notes(id) ON DELETE RESTRICT;


--
-- Name: time_entries time_entries_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.time_entries
    ADD CONSTRAINT time_entries_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--


