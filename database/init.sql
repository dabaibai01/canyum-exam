-- 可以云码考试系统 数据库初始化脚本
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS keyunma_exam DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE keyunma_exam;

-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
    phone VARCHAR(20) COMMENT '手机号',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：admin/admin_user/user',
    department VARCHAR(100) COMMENT '部门',
    position VARCHAR(100) COMMENT '岗位',
    avatar VARCHAR(255) COMMENT '头像',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 题库分类表（按工种/章节分类）
CREATE TABLE categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    parent_id BIGINT DEFAULT 0 COMMENT '父分类ID',
    type VARCHAR(20) NOT NULL DEFAULT 'question' COMMENT '类型：question题库/video视频/book书籍',
    sort INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态：0禁用/1启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_parent_id (parent_id),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题库分类表';

-- 题目表
CREATE TABLE questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_id BIGINT NOT NULL COMMENT '分类ID',
    type VARCHAR(20) NOT NULL COMMENT '题型：single单选/multiple多选/judge判断/fill填空/essay简答',
    content TEXT NOT NULL COMMENT '题干内容',
    image VARCHAR(255) COMMENT '题目图片',
    analysis TEXT COMMENT '答案解析',
    difficulty TINYINT DEFAULT 1 COMMENT '难度：1简单/2中等/3困难',
    score DECIMAL(5,1) DEFAULT 1.0 COMMENT '默认分值',
    status TINYINT DEFAULT 1 COMMENT '状态：0禁用/1启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_id (category_id),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表';

-- 选项表
CREATE TABLE question_options (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    question_id BIGINT NOT NULL COMMENT '题目ID',
    label VARCHAR(10) NOT NULL COMMENT '选项标签：A/B/C/D',
    content TEXT NOT NULL COMMENT '选项内容',
    is_correct TINYINT DEFAULT 0 COMMENT '是否正确答案：0否/1是',
    sort INT DEFAULT 0 COMMENT '排序',
    INDEX idx_question_id (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='选项表';

-- 考试表
CREATE TABLE exams (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '考试名称',
    description TEXT COMMENT '考试说明',
    category_id BIGINT COMMENT '关联分类',
    total_score DECIMAL(5,1) DEFAULT 100.0 COMMENT '总分',
    duration INT COMMENT '考试时长（分钟）',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    question_count INT DEFAULT 0 COMMENT '题目数量',
    pass_score DECIMAL(5,1) DEFAULT 60.0 COMMENT '及格分数',
    status TINYINT DEFAULT 0 COMMENT '状态：0草稿/1发布/2结束',
    created_by BIGINT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_id (category_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试表';

-- 考试题目关联表
CREATE TABLE exam_questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    exam_id BIGINT NOT NULL COMMENT '考试ID',
    question_id BIGINT NOT NULL COMMENT '题目ID',
    score DECIMAL(5,1) DEFAULT 1.0 COMMENT '本题分值',
    sort INT DEFAULT 0 COMMENT '排序',
    UNIQUE KEY uk_exam_question (exam_id, question_id),
    INDEX idx_exam_id (exam_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试题目关联表';

-- 用户答题记录表
CREATE TABLE user_answers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    exam_id BIGINT COMMENT '考试ID（刷题模式为空）',
    question_id BIGINT NOT NULL COMMENT '题目ID',
    user_answer TEXT COMMENT '用户答案',
    is_correct TINYINT DEFAULT 0 COMMENT '是否正确：0错/1对',
    score DECIMAL(5,1) DEFAULT 0 COMMENT '得分',
    answer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '答题时间',
    INDEX idx_user_id (user_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_question_id (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户答题记录表';

-- 错题本表
CREATE TABLE wrong_questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    question_id BIGINT NOT NULL COMMENT '题目ID',
    wrong_count INT DEFAULT 1 COMMENT '错误次数',
    last_wrong_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最近错误时间',
    mastered TINYINT DEFAULT 0 COMMENT '是否已掌握：0否/1是',
    UNIQUE KEY uk_user_question (user_id, question_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本表';

-- 视频教学表
CREATE TABLE videos (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '视频标题',
    description TEXT COMMENT '视频简介',
    category_id BIGINT COMMENT '分类ID',
    video_url VARCHAR(500) NOT NULL COMMENT '视频地址',
    cover_image VARCHAR(255) COMMENT '封面图',
    duration INT COMMENT '时长（秒）',
    sort INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态：0禁用/1启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频教学表';

-- 书籍表
CREATE TABLE books (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '书名',
    author VARCHAR(100) COMMENT '作者',
    description TEXT COMMENT '简介',
    category_id BIGINT COMMENT '分类ID',
    cover_image VARCHAR(255) COMMENT '封面图',
    file_url VARCHAR(500) COMMENT '文件地址',
    sort INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态：0禁用/1启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='书籍表';

-- 初始化默认管理员账号（密码：admin123）
INSERT INTO users (username, password_hash, real_name, role) VALUES
('admin', '$2a$10$QoabbY9tGCjAG6a7k8o.zO35VD.p067WH90HU6Z/9Veh7SJg4vw8m', '管理员', 'admin');

-- 初始化默认分类
INSERT INTO categories (name, parent_id, type, sort) VALUES
('学员定职刷题', 0, 'question', 1),
('提职副司机刷题', 0, 'question', 2),
('提职司机刷题', 0, 'question', 3),
('技师高级技师刷题', 0, 'question', 4),
('月度抽考刷题', 0, 'question', 5),
('视频教学', 0, 'video', 10),
('业务书籍', 0, 'book', 11);
