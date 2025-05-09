PGDMP  2                    }           authent_leg    17.4 (Debian 17.4-1.pgdg120+2)    17.4     (           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            )           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            *           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            +           1262    16384    authent_leg    DATABASE     v   CREATE DATABASE authent_leg WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';
    DROP DATABASE authent_leg;
                     bddauthlona    false                        2615    16385    authentification    SCHEMA         CREATE SCHEMA authentification;
    DROP SCHEMA authentification;
                     bddauthlona    false            �            1259    16387    usager    TABLE     �  CREATE TABLE authentification.usager (
    id integer NOT NULL,
    utilisateur character varying(255) NOT NULL,
    pwd character varying(255) NOT NULL,
    type character varying(10),
    date_creat_pwd date DEFAULT CURRENT_DATE,
    validation boolean DEFAULT false,
    CONSTRAINT user_type_check CHECK (((type)::text = ANY ((ARRAY['interne'::character varying, 'externe'::character varying])::text[])))
);
 $   DROP TABLE authentification.usager;
       authentification         heap r       bddauthlona    false    6            �            1259    16386    user_id_seq    SEQUENCE     �   CREATE SEQUENCE authentification.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE authentification.user_id_seq;
       authentification               bddauthlona    false    219    6            ,           0    0    user_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE authentification.user_id_seq OWNED BY authentification.usager.id;
          authentification               bddauthlona    false    218            �           2604    16390 	   usager id    DEFAULT     x   ALTER TABLE ONLY authentification.usager ALTER COLUMN id SET DEFAULT nextval('authentification.user_id_seq'::regclass);
 B   ALTER TABLE authentification.usager ALTER COLUMN id DROP DEFAULT;
       authentification               bddauthlona    false    219    218    219            %          0    16387    usager 
   TABLE DATA           b   COPY authentification.usager (id, utilisateur, pwd, type, date_creat_pwd, validation) FROM stdin;
    authentification               bddauthlona    false    219   �       -           0    0    user_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('authentification.user_id_seq', 12, true);
          authentification               bddauthlona    false    218            �           2606    16397    usager user_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY authentification.usager
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY authentification.usager DROP CONSTRAINT user_pkey;
       authentification                 bddauthlona    false    219            �           2606    16399    usager user_utilisateur_key 
   CONSTRAINT     g   ALTER TABLE ONLY authentification.usager
    ADD CONSTRAINT user_utilisateur_key UNIQUE (utilisateur);
 O   ALTER TABLE ONLY authentification.usager DROP CONSTRAINT user_utilisateur_key;
       authentification                 bddauthlona    false    219            %   9  x���1�1F���`��.i ��&E�E��zSm"M3c|~~�zl]��0j�2&��v���V�aKH񳓊�DUĢ��Y����ք�`W����ۦ���v�޾�my����������7�ot�~��r���Mq�:��yۚ���4�;�vD[A'���|Y�dYD*@p�mQ9��uj^�T��o[5�������㾻�@^�[J�X�0�[Y)T��@����x9��ғ^��Ҍy7��N,��*kkL�yw���dw���ylrT�0o���,��s��`2�`� ,m�	f����<�o�?&j�{��m��%�#�!�����N���{��	��={���c{�s=��t��p])��n�dm�@k̾��,H���g��������z��ќ�9�c��s��Ĩ0fI��}(o57Nj�
�ȅ�O�u'��U�Y߈9Iq����f�Z2*!<jT����-w$��H�{q\�נ^C�E��.���\2k�kd��H���EC��j�N�rW���Җ�0D��o.;;�s�x/��Z�yh�}��z�~.�q�     