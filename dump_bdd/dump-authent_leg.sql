PGDMP      ,    	            }           authent_leg    17.4 (Debian 17.4-1.pgdg120+2)    17.4     (           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
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
    authentification               bddauthlona    false    219   �       -           0    0    user_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('authentification.user_id_seq', 17, true);
          authentification               bddauthlona    false    218            �           2606    16397    usager user_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY authentification.usager
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY authentification.usager DROP CONSTRAINT user_pkey;
       authentification                 bddauthlona    false    219            �           2606    16399    usager user_utilisateur_key 
   CONSTRAINT     g   ALTER TABLE ONLY authentification.usager
    ADD CONSTRAINT user_utilisateur_key UNIQUE (utilisateur);
 O   ALTER TABLE ONLY authentification.usager DROP CONSTRAINT user_utilisateur_key;
       authentification                 bddauthlona    false    219            %   �  x���=��6Fc�]օwq�@��\��F��q��UJ�R� ~��ǩ�ʕ����(ṷ́K=!-�$����f~� ^����� �Z�\��
SO�4vF�:G����S�|��?�! ����/y���
��BӹS�R.����M��{5h���p��tB�~�B���,L�V�3U�/��U���4�}����\S�o�}L����hq�j�=�@1��kC���H�8?m�z�1��(;��޹t�<�nX&�밝�m,�L��zi�+�Cl=>9*�T]���{6X�r5��sl���t�uTM�f�������]D�]v�,o��f��x'������:@"�=���uǾ���ύSf��|���v\�%A�1�bR��A����~��?^��F��W��i:t�qL#���;�3*�YV��G�ʲ=\3��F0�qr��nR�j�����$D!�mT���!<۩�ӧ���lV�#�z��k�QC�͆�f��>��w#�G2�Ǳ.:�U��>��T�w�t�>��Yo�/9)=��w�?����\�m�]Q�&7ʹ��mHkNv5��x>��f��L�Nk����t��j��p�K���IvlkMi�5 ׺�ݙ����̞;F�L��dI��lU`g��<Ue[���]���B跞�|&�w���&%L��L�<�m���"W�=#��0����
��/B������K�s���z��'��     