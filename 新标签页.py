# 这是新的标签页实现代码，会添加到main_window.py中

def create_background_tab(self, parent):
    """背景标签页"""
    # 默认背景
    default_label = tk.Label(
        parent,
        text='默认背景',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    default_label.pack(fill=tk.X, padx=16, pady=(16, 8))
    
    # 默认背景网格
    bg_grid = tk.Frame(parent, bg=COLORS['panel_bg'])
    bg_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    for idx, bg in enumerate(DEFAULT_BACKGROUNDS):
        row = idx // 4
        col = idx % 4
        btn = tk.Button(
            bg_grid,
            bg=bg['color'],
            width=6,
            height=3,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground=COLORS['separator'],
            cursor='hand2',
            command=lambda c=bg['color']: self.set_background_color(c)
        )
        btn.grid(row=row, column=col, padx=4, pady=4)
        
        # 显示名称
        name_label = tk.Label(
            bg_grid,
            text=bg['name'],
            font=('SF Pro Text', 9),
            bg=COLORS['panel_bg'],
            fg=COLORS['text_secondary']
        )
        name_label.grid(row=row+1, column=col, padx=2, pady=(0, 8))
    
    # 分隔线
    sep = tk.Frame(parent, bg=COLORS['separator'], height=1)
    sep.pack(fill=tk.X, padx=16, pady=12)
    
    # 自定义颜色
    custom_label = tk.Label(
        parent,
        text='自定义颜色',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    custom_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    color_frame = tk.Frame(parent, bg=COLORS['panel_bg'])
    color_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.bg_color_preview = tk.Frame(
        color_frame,
        bg=self.background_color,
        width=60,
        height=60,
        relief=tk.SUNKEN,
        bd=2
    )
    self.bg_color_preview.pack(side=tk.LEFT, padx=(0, 12))
    
    tk.Button(
        color_frame,
        text='选择颜色',
        command=self.choose_background_color,
        bg='white',
        fg=COLORS['text_primary'],
        font=('SF Pro Text', 11),
        padx=16,
        pady=12,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS['separator'],
        cursor='hand2'
    ).pack(side=tk.LEFT)
    
    # 分隔线
    sep2 = tk.Frame(parent, bg=COLORS['separator'], height=1)
    sep2.pack(fill=tk.X, padx=16, pady=12)
    
    # 上传背景图片
    upload_label = tk.Label(
        parent,
        text='背景图片',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    upload_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    tk.Button(
        parent,
        text='📁 上传背景图片',
        command=self.upload_background_image,
        bg=COLORS['accent'],
        fg='white',
        font=('SF Pro Text', 12, 'bold'),
        pady=12,
        relief=tk.FLAT,
        bd=0,
        cursor='hand2'
    ).pack(fill=tk.X, padx=16, pady=(0, 8))
    
    tk.Button(
        parent,
        text='🗑️ 清除背景图片',
        command=self.clear_background_image,
        bg='white',
        fg=COLORS['danger'],
        font=('SF Pro Text', 11),
        pady=10,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS['separator'],
        cursor='hand2'
    ).pack(fill=tk.X, padx=16)

def create_border_tab(self, parent):
    """边框标签页 - 自定义配置"""
    # 创建滚动区域
    canvas = tk.Canvas(parent, bg=COLORS['panel_bg'], highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient='vertical', command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=COLORS['panel_bg'])
    
    scroll_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )
    
    canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 1. 形状选择
    shape_label = tk.Label(
        scroll_frame,
        text='形状',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    shape_label.pack(fill=tk.X, padx=16, pady=(16, 8))
    
    shape_grid = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
    shape_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.border_shape_buttons = {}
    for idx, shape in enumerate(BORDER_SHAPES):
        btn = tk.Button(
            shape_grid,
            text=f"{shape['icon']}\n{shape['name']}",
            command=lambda s=shape['id']: self.set_border_shape(s),
            bg='white' if shape['id'] == self.border_config['shape'] else COLORS['hover'],
            fg=COLORS['accent'] if shape['id'] == self.border_config['shape'] else COLORS['text_primary'],
            font=('SF Pro Text', 10),
            width=8,
            pady=8,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['separator'],
            cursor='hand2'
        )
        btn.grid(row=0, column=idx, padx=3)
        self.border_shape_buttons[shape['id']] = btn
    
    # 2. 线条样式
    line_label = tk.Label(
        scroll_frame,
        text='线条样式',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    line_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    line_grid = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
    line_grid.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.border_line_buttons = {}
    for idx, line_style in enumerate(BORDER_LINE_STYLES):
        btn = tk.Button(
            line_grid,
            text=line_style['name'],
            command=lambda l=line_style['id']: self.set_border_line_style(l),
            bg='white' if line_style['id'] == self.border_config['line_style'] else COLORS['hover'],
            fg=COLORS['accent'] if line_style['id'] == self.border_config['line_style'] else COLORS['text_primary'],
            font=('SF Pro Text', 10),
            width=8,
            pady=8,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['separator'],
            cursor='hand2'
        )
        btn.grid(row=0, column=idx, padx=3)
        self.border_line_buttons[line_style['id']] = btn
    
    # 3. 粗细滑块
    width_label = tk.Label(
        scroll_frame,
        text='粗细',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    width_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    width_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
    width_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.border_width_scale = tk.Scale(
        width_frame,
        from_=1,
        to=50,
        orient=tk.HORIZONTAL,
        command=self.on_border_width_change,
        bg=COLORS['panel_bg'],
        highlightthickness=0
    )
    self.border_width_scale.set(self.border_config['width'])
    self.border_width_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    self.border_width_value = tk.Label(
        width_frame,
        text=f"{self.border_config['width']}px",
        font=('SF Pro Text', 11, 'bold'),
        bg=COLORS['panel_bg'],
        width=6
    )
    self.border_width_value.pack(side=tk.LEFT)
    
    # 4. 圆角度数滑块
    radius_label = tk.Label(
        scroll_frame,
        text='圆角',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    radius_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    radius_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
    radius_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.border_radius_scale = tk.Scale(
        radius_frame,
        from_=0,
        to=100,
        orient=tk.HORIZONTAL,
        command=self.on_border_radius_change,
        bg=COLORS['panel_bg'],
        highlightthickness=0
    )
    self.border_radius_scale.set(self.border_config['radius'])
    self.border_radius_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    self.border_radius_value = tk.Label(
        radius_frame,
        text=f"{self.border_config['radius']}px",
        font=('SF Pro Text', 11, 'bold'),
        bg=COLORS['panel_bg'],
        width=6
    )
    self.border_radius_value.pack(side=tk.LEFT)
    
    # 5. 颜色选择
    color_label = tk.Label(
        scroll_frame,
        text='颜色',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    color_label.pack(fill=tk.X, padx=16, pady=(8, 8))
    
    color_frame = tk.Frame(scroll_frame, bg=COLORS['panel_bg'])
    color_frame.pack(fill=tk.X, padx=16, pady=(0, 16))
    
    self.border_color_preview = tk.Frame(
        color_frame,
        bg=self.border_config['color'],
        width=60,
        height=60,
        relief=tk.SUNKEN,
        bd=2
    )
    self.border_color_preview.pack(side=tk.LEFT, padx=(0, 12))
    
    tk.Button(
        color_frame,
        text='选择颜色',
        command=self.choose_border_color,
        bg='white',
        fg=COLORS['text_primary'],
        font=('SF Pro Text', 11),
        padx=16,
        pady=12,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS['separator'],
        cursor='hand2'
    ).pack(side=tk.LEFT)
    
    # 6. 应用边框按钮
    tk.Button(
        scroll_frame,
        text='✓ 应用边框',
        command=self.apply_custom_border,
        bg=COLORS['accent'],
        fg='white',
        font=('SF Pro Text', 13, 'bold'),
        pady=14,
        relief=tk.FLAT,
        bd=0,
        cursor='hand2'
    ).pack(fill=tk.X, padx=16, pady=(16, 16))
    
    # 打包滚动组件
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def create_sticker_tab(self, parent):
    """贴纸标签页"""
    sticker_label = tk.Label(
        parent,
        text='点击添加贴纸',
        font=('SF Pro Display', 13, 'bold'),
        bg=COLORS['panel_bg'],
        fg=COLORS['text_primary'],
        anchor='w'
    )
    sticker_label.pack(fill=tk.X, padx=16, pady=(16, 8))
    
    # 贴纸网格
    sticker_grid = tk.Frame(parent, bg=COLORS['panel_bg'])
    sticker_grid.pack(fill=tk.X, padx=12, pady=(0, 16))
    
    for idx, sticker in enumerate(STICKER_LIST):
        row = idx // 4
        col = idx % 4
        
        # 优先使用PNG图片，否则使用emoji
        if sticker['id'] in self.sticker_images:
            btn = tk.Button(
                sticker_grid,
                image=self.sticker_images[sticker['id']],
                command=lambda s=sticker: self.add_sticker(s),
                bg='white',
                activebackground=COLORS['hover'],
                relief=tk.FLAT,
                width=40,
                height=40,
                bd=0,
                highlightthickness=1,
                highlightbackground=COLORS['separator'],
                cursor='hand2'
            )
        else:
            btn = tk.Button(
                sticker_grid,
                text=sticker['emoji'],
                font=('Apple Color Emoji', 28),
                command=lambda s=sticker: self.add_sticker(s),
                bg='white',
                activebackground=COLORS['hover'],
                relief=tk.FLAT,
                width=2,
                height=1,
                bd=0,
                highlightthickness=1,
                highlightbackground=COLORS['separator'],
                cursor='hand2'
            )
        btn.grid(row=row, column=col, padx=4, pady=4)
