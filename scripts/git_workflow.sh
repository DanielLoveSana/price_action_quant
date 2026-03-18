#!/bin/bash
# Git工作流脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数定义
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 检查是否在Git仓库中
check_git_repo() {
    if [ ! -d ".git" ]; then
        print_error "当前目录不是Git仓库"
        exit 1
    fi
}

# 主菜单
show_menu() {
    print_header "Price Action Quant - Git工作流"
    echo "1. 检查状态"
    echo "2. 添加所有更改"
    echo "3. 提交当前阶段"
    echo "4. 推送到远程仓库"
    echo "5. 拉取最新更改"
    echo "6. 查看提交历史"
    echo "7. 创建功能分支"
    echo "8. 设置远程仓库"
    echo "9. 退出"
    echo -n "请选择操作 [1-9]: "
}

# 检查状态
check_status() {
    print_header "Git状态"
    git status
}

# 添加所有更改
add_all_changes() {
    print_header "添加所有更改"
    git add .
    print_success "已添加所有更改"
    git status --short
}

# 提交当前阶段
commit_changes() {
    print_header "提交更改"
    
    echo "请选择提交类型:"
    echo "1. Phase完成提交"
    echo "2. 功能开发提交"
    echo "3. Bug修复提交"
    echo "4. 文档更新"
    echo "5. 自定义提交信息"
    echo -n "选择 [1-5]: "
    read commit_type
    
    case $commit_type in
        1)
            echo -n "输入Phase编号 (如1.3): "
            read phase_num
            echo -n "输入Phase描述: "
            read phase_desc
            commit_msg="Phase $phase_num: $phase_desc"
            
            echo -n "输入详细更改说明 (空行结束): "
            echo "(按Ctrl+D结束输入)"
            detailed_msg=$(cat)
            
            full_msg="$commit_msg\n\n$detailed_msg"
            ;;
        2)
            echo -n "输入功能名称: "
            read feature_name
            echo -n "输入功能描述: "
            read feature_desc
            commit_msg="feat: $feature_name"
            
            echo -n "输入详细更改说明 (空行结束): "
            echo "(按Ctrl+D结束输入)"
            detailed_msg=$(cat)
            
            full_msg="$commit_msg\n\n$feature_desc\n\n$detailed_msg"
            ;;
        3)
            echo -n "输入Bug描述: "
            read bug_desc
            commit_msg="fix: $bug_desc"
            full_msg="$commit_msg"
            ;;
        4)
            echo -n "输入文档更新描述: "
            read doc_desc
            commit_msg="docs: $doc_desc"
            full_msg="$commit_msg"
            ;;
        5)
            echo -n "输入提交信息: "
            read custom_msg
            full_msg="$custom_msg"
            ;;
        *)
            print_error "无效选择"
            return 1
            ;;
    esac
    
    # 提交
    echo -e "$full_msg" | git commit -F -
    print_success "提交完成"
}

# 推送到远程仓库
push_to_remote() {
    print_header "推送到远程仓库"
    
    # 检查远程仓库
    if ! git remote | grep -q origin; then
        print_error "未设置远程仓库"
        echo "请先运行选项8设置远程仓库"
        return 1
    fi
    
    echo -n "输入分支名称 (默认: main): "
    read branch
    branch=${branch:-main}
    
    echo -n "是否强制推送? (y/N): "
    read force_push
    
    if [[ $force_push =~ ^[Yy]$ ]]; then
        git push origin $branch --force
        print_info "强制推送完成"
    else
        git push origin $branch
        print_success "推送完成"
    fi
}

# 拉取最新更改
pull_latest() {
    print_header "拉取最新更改"
    
    if ! git remote | grep -q origin; then
        print_error "未设置远程仓库"
        return 1
    fi
    
    echo -n "输入分支名称 (默认: main): "
    read branch
    branch=${branch:-main}
    
    git pull origin $branch
    print_success "拉取完成"
}

# 查看提交历史
view_history() {
    print_header "提交历史"
    
    echo "选择查看方式:"
    echo "1. 简洁模式"
    echo "2. 详细模式"
    echo "3. 图形模式"
    echo -n "选择 [1-3]: "
    read view_mode
    
    case $view_mode in
        1)
            git log --oneline -10
            ;;
        2)
            git log --pretty=format:"%C(yellow)%h %C(blue)%ad %C(green)%an %C(reset)%s" --date=short -10
            ;;
        3)
            git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit -10
            ;;
        *)
            git log --oneline -10
            ;;
    esac
}

# 创建功能分支
create_feature_branch() {
    print_header "创建功能分支"
    
    echo -n "输入功能分支名称: "
    read branch_name
    
    # 清理分支名称
    branch_name=$(echo "$branch_name" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
    branch_name="feature/$branch_name"
    
    git checkout -b $branch_name
    print_success "已创建并切换到分支: $branch_name"
}

# 设置远程仓库
setup_remote() {
    print_header "设置远程仓库"
    
    echo "请选择:"
    echo "1. 添加新的远程仓库"
    echo "2. 查看当前远程仓库"
    echo "3. 移除远程仓库"
    echo -n "选择 [1-3]: "
    read remote_choice
    
    case $remote_choice in
        1)
            echo -n "输入远程仓库URL: "
            read remote_url
            echo -n "输入远程仓库名称 (默认: origin): "
            read remote_name
            remote_name=${remote_name:-origin}
            
            git remote add $remote_name $remote_url
            print_success "已添加远程仓库: $remote_name -> $remote_url"
            ;;
        2)
            git remote -v
            ;;
        3)
            echo -n "输入要移除的远程仓库名称: "
            read remote_name
            git remote remove $remote_name
            print_success "已移除远程仓库: $remote_name"
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
}

# 主程序
main() {
    check_git_repo
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            1) check_status ;;
            2) add_all_changes ;;
            3) commit_changes ;;
            4) push_to_remote ;;
            5) pull_latest ;;
            6) view_history ;;
            7) create_feature_branch ;;
            8) setup_remote ;;
            9)
                print_success "退出Git工作流"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                ;;
        esac
        
        echo
        echo "按Enter继续..."
        read
    done
}

# 运行主程序
main "$@"